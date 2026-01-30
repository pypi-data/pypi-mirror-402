from odoo import models

from bi_sc_client.services.invoice_pdf_regenerate import InvoicePDFRegenerator


class AccountInvoiceRegeneratePDF(models.TransientModel):
    _name = "account.invoice.regenerate.pdf"
    _description = "Regenerate PDF"

    def run(self):
        invoice = self.env["account.move"].browse(self.env.context["active_id"])
        InvoicePDFRegenerator(invoice_numbers=[invoice.name]).run()
