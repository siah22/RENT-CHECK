from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import owner_agent_required
from engagement.forms import ReportForm, ReviewForm, ViewingRequestForm
from engagement.models import Favorite

from .forms import PropertyForm, PropertySearchForm
from .models import Property, PropertyImage


def browse_properties(request):
    form = PropertySearchForm(request.GET or None)
    listings = Property.objects.filter(
        is_available=True, is_rented=False, verification_status=Property.VerificationStatus.APPROVED
    ).prefetch_related("images", "amenities")

    if form.is_valid():
        data = form.cleaned_data
        if data.get("q"):
            q = data["q"]
            listings = listings.filter(
                Q(title__icontains=q) | Q(city__icontains=q) | Q(region__icontains=q)
                | Q(address__icontains=q)
            )
        if data.get("property_type"):
            listings = listings.filter(property_type=data["property_type"])
        if data.get("min_price") is not None:
            listings = listings.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            listings = listings.filter(price__lte=data["max_price"])
        if data.get("bedrooms") is not None:
            listings = listings.filter(bedrooms__gte=data["bedrooms"])
        if data.get("bathrooms") is not None:
            listings = listings.filter(bathrooms__gte=data["bathrooms"])
        if data.get("min_size") is not None:
            listings = listings.filter(size_sqm__gte=data["min_size"])
        if data.get("amenities"):
            for amenity in data["amenities"]:
                listings = listings.filter(amenities=amenity)
        listings = listings.order_by(data.get("sort") or "-date_listed")
    else:
        listings = listings.order_by("-date_listed")

    listings = listings.distinct()
    paginator = Paginator(listings, 9)
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
    })


def property_detail(request, pk):
    property_obj = get_object_or_404(Property.objects.prefetch_related(
        "images", "amenities", "reviews__user"
    ), pk=pk)

    is_owner = request.user.is_authenticated and property_obj.owner_id == request.user.id
    if not property_obj.is_verified and not is_owner and not (
        request.user.is_authenticated and request.user.is_admin_role
    ):
        messages.warning(request, "This listing is awaiting verification and is only visible to its owner and admins.")

    is_favorited = (
        request.user.is_authenticated
        and Favorite.objects.filter(tenant=request.user, property=property_obj).exists()
    )

    return render(request, "properties/detail.html", {
        "property": property_obj,
        "is_owner": is_owner,
        "is_favorited": is_favorited,
        "viewing_form": ViewingRequestForm(),
        "report_form": ReportForm(),
        "review_form": ReviewForm(),
        "share_url": request.build_absolute_uri(),
    })


@owner_agent_required
def my_properties(request):
    listings = Property.objects.filter(owner=request.user).prefetch_related("images")
    return render(request, "properties/my_properties.html", {"listings": listings})


@owner_agent_required
def create_property(request):
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            form.save_m2m()
            for image in request.FILES.getlist("images"):
                PropertyImage.objects.create(property=property_obj, image=image)
            messages.success(request, "Property listed successfully. It will appear once verified by an administrator.")
            return redirect("properties:my_properties")
    else:
        form = PropertyForm()
    return render(request, "properties/property_form.html", {"form": form, "title": "List a Property"})


@owner_agent_required
def edit_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            for image in request.FILES.getlist("images"):
                PropertyImage.objects.create(property=property_obj, image=image)
            messages.success(request, "Property updated.")
            return redirect("properties:my_properties")
    else:
        form = PropertyForm(instance=property_obj)
    return render(request, "properties/property_form.html", {
        "form": form, "title": "Edit Property", "property": property_obj,
    })


@owner_agent_required
def delete_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        property_obj.delete()
        messages.success(request, "Property deleted.")
        return redirect("properties:my_properties")
    return render(request, "properties/property_confirm_delete.html", {"property": property_obj})


@owner_agent_required
def delete_property_image(request, pk):
    image = get_object_or_404(PropertyImage, pk=pk, property__owner=request.user)
    property_id = image.property_id
    image.delete()
    messages.success(request, "Image removed.")
    return redirect("properties:edit", pk=property_id)


@owner_agent_required
def toggle_rented(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    property_obj.is_rented = not property_obj.is_rented
    property_obj.is_available = not property_obj.is_rented
    property_obj.save()
    messages.success(
        request,
        "Marked as rented." if property_obj.is_rented else "Marked as available.",
    )
    return redirect("properties:my_properties")
