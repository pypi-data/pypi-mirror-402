# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class MixinEmployeeBankAccount(models.AbstractModel):
    _name = "mixin.employee_bank_account"
    _inherit = [
        "mixin.employee_document",
    ]
    _description = "Mixin for Document With Employee Bank Account"

    allowed_bank_account_ids = fields.Many2many(
        string="Allowed Bank Accounts",
        comodel_name="res.partner.bank",
        compute="_compute_allowed_bank_account_ids",
        compute_sudo=True,
        store=False,
    )
    employee_bank_account_id = fields.Many2one(
        string="Employee Bank Account",
        comodel_name="res.partner.bank",
        readonly=True,
        states={"draft": [("readonly", False)]},
        compute_sudo=True,
    )

    @api.depends(
        "employee_id",
    )
    def _compute_allowed_bank_account_ids(self):
        for record in self:
            result = False

            if record.employee_id and record.employee_id.address_home_id:
                contact = record.employee_id.address_home_id
                criteria = [
                    ("partner_id", "=", contact.id),
                ]
                result = self.env["res.partner.bank"].search(criteria).ids
            record.allowed_bank_account_ids = result

    @api.onchange(
        "employee_id",
    )
    def onchange_employee_bank_account_id(self):
        self.employee_bank_account_id = False
        if self.employee_id:
            self.employee_bank_account_id = self.employee_id.bank_account_id
