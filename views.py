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
            reciver.balance += amount
            sender.balance -= amount
            reciver.save(update_fields=["balance"])
            sender.save(update_fields=["balance"])
            messages.success(self.request, "Send Money Successful")
            send_transaction_email(
                self.request.user,
                amount,
                "Money Transfer Message",
                "transactions/deposite_mail.html",
            )
            send_transaction_email(
                reciver.user,
                amount,
                "Money Revived Message",
                "transactions/deposite_mail.html",
            )

            return super().form_valid(form)
        except UserBankAccount.DoesNotExist:
            form.add_error("account_number", "Invalid Account No")
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
