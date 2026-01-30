from odoo import models, fields


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    set_uploaded_job_ids = fields.Many2many(
        comodel_name="queue.job",
        column1="account_payment_order_id",
        column2="job_id",
        string="Set as Uploaded Jobs",
        copy=False,
    )

    def generated2uploaded_job(self):
        self.ensure_one()
        if self.state != "generated":
            return
        self.generated2uploaded()

    def draft2open(self):
        super().draft2open()
        for order in self:
            for payline in order.payment_line_ids:
                if payline.move_line_id.move_id.journal_id == (
                    self.env.ref(
                        "invoice_somconnexio.customer_services_invoices_journal"
                    )
                ):
                    payline.purpose = "PHON"
