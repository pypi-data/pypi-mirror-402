# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrCashAdvanceSettlementLineInherit(models.Model):
    _inherit = "hr.cash_advance_settlement_line"

    require_expense_account = fields.Boolean(
        string="Require Expense Account",
        readonly=True,
    )
    expense_account_id = fields.Many2one(
        comodel_name="employee_expense_account",
        string="Expense Account",
        readonly=True,
    )

    def _check_expense_account(self):
        self.ensure_one()
        result = True
        if self.require_expense_account:
            if not self.expense_account_id:
                error_msg = _("No expense account")
                raise UserError(error_msg)

            if self.expense_account_id.amount_residual < 0.0:
                error_msg = _("Insuficient expense account")
                raise UserError(error_msg)
        return result

    @api.onchange(
        "product_id",
        "type_id",
    )
    def onchange_require_expense_account(self):
        result = False
        ExpType = self.env["hr.expense_type"]

        if self.type_id and self.product_id:
            expense_categories = ExpType.search(
                [
                    ("id", "=", self.type_id.id),
                ]
            )
            req_product_ids = expense_categories._get_require_expense_products()

            if self.product_id in req_product_ids:
                result = True

        self.require_expense_account = result
