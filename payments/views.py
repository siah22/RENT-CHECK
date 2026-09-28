import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import PaymentForm
from .models import Payment
from .services import confirm_from_callback, initiate_payment, query_status


@login_required
def payment_list(request):
    payments = Payment.objects.filter(user=request.user)
    return render(request, "payments/payment_list.html", {"payments": payments})


@login_required
def payment_new(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = initiate_payment(
                user=request.user,
                amount=form.cleaned_data["amount"],
                purpose=form.cleaned_data["purpose"],
                reference=form.cleaned_data["reference"],
                phone=form.cleaned_data["phone"],
                description=form.cleaned_data["description"],
            )
            if payment.status == Payment.Status.COMPLETED:
                messages.success(request, _("Payment completed successfully."))
            elif payment.status == Payment.Status.FAILED:
                messages.error(request, _("M-Pesa could not process this payment. Check the number and try again."))
            else:
                messages.info(request, _("Payment request sent. Approve it on your phone."))
            return redirect("payments:detail", pk=payment.pk)
    else:
        form = PaymentForm()
    return render(request, "payments/payment_form.html", {"form": form})


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    if request.method == "POST":
        if payment.status == Payment.Status.PENDING:
            query_status(payment)
            messages.info(request, _("Payment status refreshed."))
        return redirect("payments:detail", pk=pk)
    return render(request, "payments/payment_detail.html", {"payment": payment})


@csrf_exempt
@require_POST
def mpesa_callback(request, token):
    if settings.MPESA_CALLBACK_TOKEN and token != settings.MPESA_CALLBACK_TOKEN:
        return JsonResponse({"error": "invalid token"}, status=403)
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        payload = {}
    confirm_from_callback(payload)
    return JsonResponse({"output_ResponseCode": "INS-000000", "output_ResponseDesc": "SUCCESS"})