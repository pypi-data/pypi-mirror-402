from odoo.addons.somconnexio.tests.sc_test_case import SCTestCase
from unittest.mock import patch


class TestAccountInvoiceRegeneratePDFWizard(SCTestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.invoice = self.browse_ref("invoice_somconnexio.invoice_bi_demo")

    @patch(
        "odoo.addons.invoice_somconnexio.wizards.account_invoice_regenerate_PDF.account_invoice_regenerate_PDF.InvoicePDFRegenerator"  # noqa
    )
    def test_import_invoice_payment_ok(self, mock_invoice_pdf_regenerate):
        wizard = (
            self.env["account.invoice.regenerate.pdf"]
            .with_context(active_id=self.invoice.id)
            .create({})
        )
        wizard.run()

        mock_invoice_pdf_regenerate.assert_called_once_with(
            invoice_numbers=[self.invoice.name],
        )
        mock_invoice_pdf_regenerate.return_value.run.assert_called_once()
