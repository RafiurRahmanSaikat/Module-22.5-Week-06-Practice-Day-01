from datetime import datetime

from accounts.models import UserBankAccount
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from .constants import DEPOSIT, LOAN, LOAN_PAID, TRANSFER_MONEY, WITHDRAW
from .forms import DepositForm, LoanRequestForm, TransferMoneyForm, WithdrawForm
from .models import TransactionModel

# Create your views here.from django.views import generic


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = "transactions/transaction.html"
    model = TransactionModel
    title = ""
    success_url = reverse_lazy("transaction_report")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"account": self.request.user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context.update({"title": self.title})
        return context


class TransferMoneyView(TransactionCreateMixin):
    form_class = TransferMoneyForm
    template_name = "transactions/transfermoney.html"
    title = "Transfer Money"
    success_url = reverse_lazy("transaction_report")

    def get_initial(self):
        initial = {"transaction_type": TRANSFER_MONEY}
        return initial

    def form_valid(self, form):
        account_number = form.cleaned_data.get("account_number")
        amount = form.cleaned_data.get("amount")
        sender = self.request.user.account

        try:
            reciver = UserBankAccount.objects.get(account_number=account_number)
            if sender.balance < amount:
                messages.error(self.request, "Insufficient Balance")
                return super().form_invalid(form)
            reciver.balance += amount
            sender.balance -= amount
            reciver.save(update_fields=["balance"])
            sender.save(update_fields=["balance"])
            messages.success(self.request, "Send Money Successful")

            return super().form_valid(form)
        except UserBankAccount.DoesNotExist:
            messages.error(self.request, "Invalid Account No")
            return super().form_invalid(form)


class WithdrawView(TransactionCreateMixin):
    title = "Withdraw"
    form_class = WithdrawForm

    def get_initial(self):
        return {"transaction_type": WITHDRAW}

    def form_valid(self, form):
        account = self.request.user.account
        amount = form.cleaned_data["amount"]

        bank_balance = UserBankAccount.objects.aggregate(total_balance=Sum("balance"))[
            "total_balance"
        ]

        if bank_balance == 0 or bank_balance is None or bank_balance < amount:
            messages.warning(self.request, "Bank is Bankrupt")
            return self.form_invalid(form)

        account.balance -= amount
        account.save(update_fields=["balance"])
        messages.success(self.request, f"{amount} Tk successfully withdrawn")

        return super().form_valid(form)
