from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Property, PropertyImage
from .forms import PropertyForm

@login_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            try:
                property_obj = form.save(commit=False)
                property_obj.owner = request.user
                property_obj.save()

                # Process uploaded images safely
                images = request.FILES.getlist('images')
                for idx, image_file in enumerate(images):
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        is_primary=(idx == 0)
                    )

                messages.success(request, 'Property created successfully!')
                return redirect('properties:detail', pk=property_obj.pk)
            except Exception as e:
                messages.error(request, f'An error occurred while creating the property: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm()

    return render(request, 'properties/property_form.html', {'form': form})