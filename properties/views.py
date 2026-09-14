from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from engagement.models import Favorite
from .models import Property, PropertyImage
from .forms import PropertyForm

def browse_properties(request):
    """List all available properties."""
    properties = Property.objects.filter(is_available=True)
    return render(request, 'properties/browse.html', {'properties': properties})

def property_detail(request, pk):
    """Display details for a single property."""
    property_obj = get_object_or_404(Property, pk=pk)
    is_owner = request.user == property_obj.owner
    is_favorited = (
        request.user.is_authenticated
        and Favorite.objects.filter(tenant=request.user, property=property_obj).exists()
    )
    share_url = property_obj.get_absolute_url()
    return render(request, 'properties/detail.html', {
        'property': property_obj,
        'is_owner': is_owner,
        'is_favorited': is_favorited,
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
        messages.success(request, f'Property marked as {status}.')
    return redirect('properties:my_properties')