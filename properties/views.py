from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from engagement.models import Application, Favorite
from engagement.utils import notify
from .models import Property, PropertyImage
from .forms import PropertyForm, PropertySearchForm

def browse_properties(request):
    """List available properties, honoring the sidebar search filters."""
    form = PropertySearchForm(request.GET)

    # Regular listings vanish once rented; Airbnb/short-stay listings stay
    # visible but display a "Booked" badge instead of booking functionality.
    properties = Property.objects.filter(
        is_available=True,
        verification_status=Property.VerificationStatus.APPROVED,
    ).filter(
        Q(is_rented=False) | Q(property_type=Property.PropertyType.BNB)
    ).prefetch_related("images")

    if form.is_valid():
        data = form.cleaned_data

        keyword = (data.get("q") or "").strip()
        if keyword:
            properties = properties.filter(
                Q(title__icontains=keyword) |
                Q(city__icontains=keyword) |
                Q(region__icontains=keyword) |
                Q(address__icontains=keyword)
            )

        if data.get("property_type"):
            properties = properties.filter(property_type=data["property_type"])
        if data.get("min_price") is not None:
            properties = properties.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            properties = properties.filter(price__lte=data["max_price"])
        if data.get("bedrooms"):
            properties = properties.filter(bedrooms__gte=data["bedrooms"])
        if data.get("bathrooms"):
            properties = properties.filter(bathrooms__gte=data["bathrooms"])
        if data.get("min_size") is not None:
            properties = properties.filter(size_sqm__gte=data["min_size"])

        amenities = data.get("amenities")
        if amenities:
            properties = properties.filter(amenities__in=amenities).distinct()

        sort_key = data.get("sort")
        allowed_sorts = {"-date_listed", "price", "-price", "-size_sqm"}
        properties = properties.order_by(sort_key if sort_key in allowed_sorts else "-date_listed")
    else:
        properties = properties.order_by("-date_listed")

    paginator = Paginator(properties, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(tenant=request.user).values_list("property_id", flat=True)
        )

    return render(request, "properties/browse.html", {
        "form": form,
        "page_obj": page_obj,
        "favorite_ids": favorite_ids,
        "query_string": _strip_page(request.GET.urlencode()),
    })


def _strip_page(querystring):
    params = querystring.split("&") if querystring else []
    kept = [p for p in params if p and not p.startswith("page=")]
    return "&".join(kept)

def property_detail(request, pk):
    """Display details for a single property."""
    property_obj = get_object_or_404(Property, pk=pk)
    is_owner = request.user == property_obj.owner
    is_favorited = (
        request.user.is_authenticated
        and Favorite.objects.filter(tenant=request.user, property=property_obj).exists()
    )
    user_application = None
    if request.user.is_authenticated and not is_owner:
        user_application = property_obj.applications.filter(tenant=request.user).first()
    share_url = property_obj.get_absolute_url()
    return render(request, 'properties/detail.html', {
        'property': property_obj,
        'is_owner': is_owner,
        'is_favorited': is_favorited,
        'user_application': user_application,
        'share_url': share_url,
    })

@login_required
def property_create(request):
    """Handle new property creation and file uploads safely."""
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            try:
                property_obj = form.save(commit=False)
                property_obj.owner = request.user
                property_obj.save()

                # Safely save uploaded images
                images = request.FILES.getlist('images')
                for image_file in images:
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                    )

                messages.success(request, 'Property created successfully!')
                return redirect('properties:detail', pk=property_obj.pk)
            except Exception as e:
                messages.error(request, f'An error occurred while creating the property: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm()

    return render(request, 'properties/property_form.html', {'form': form, 'title': 'List a Property'})


@login_required
def my_properties(request):
    listings = Property.objects.filter(owner=request.user).prefetch_related('images').order_by('-date_listed')
    return render(request, 'properties/my_properties.html', {'listings': listings})


@login_required
def property_edit(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist('images')
            for image_file in images:
                PropertyImage.objects.create(property=property_obj, image=image_file)
            messages.success(request, 'Property updated successfully!')
            return redirect('properties:detail', pk=property_obj.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm(instance=property_obj)
    return render(request, 'properties/property_form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Edit Property',
    })


@login_required
def property_delete(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted.')
        return redirect('properties:my_properties')
    return render(request, 'properties/property_confirm_delete.html', {'property': property_obj})


@login_required
def property_delete_image(request, pk):
    image = get_object_or_404(PropertyImage, pk=pk, property__owner=request.user)
    property_pk = image.property.pk
    image.delete()
    messages.success(request, 'Image removed.')
    return redirect('properties:edit', pk=property_pk)


@login_required
def property_toggle_rented(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        property_obj.is_rented = not property_obj.is_rented
        property_obj.save(update_fields=['is_rented'])
        status = 'rented' if property_obj.is_rented else 'available'
        # Long-term rentals (non-BNB): close out the application pipeline so the
        # next vacancy starts fresh. Pending applicants are told the listing is gone.
        if property_obj.is_rented and not property_obj.is_bnb:
            pending = property_obj.applications.filter(status=Application.Status.PENDING)
            for app in pending:
                notify(app.tenant,
                       f"Your application for '{property_obj.title}' was closed — the listing has been rented.")
            pending.update(
                status=Application.Status.REJECTED,
                decision_note="Listing has been rented; applications are closed for this vacancy.",
                decision_date=timezone.now(),
            )
        messages.success(request, f'Property marked as {status}.')
    return redirect('properties:my_properties')