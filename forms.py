class TransferMoneyForm(TransactionForm):
    account_number = forms.IntegerField()
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        return amount
