# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, models

from odoo.addons.ssi_decorator import ssi_decorator


class HrCashAdvanceSettlement(models.Model):
    _inherit = "hr.cash_advance_settlement"

    @ssi_decorator.pre_confirm_action()
    def _check_expense_account(self):
        self.ensure_one()
        for line in self.line_ids:
            line._check_expense_account()

        return True

    @api.onchange(
        "employee_id",
        "line_ids",
        "line_ids.account_id",
        "line_ids.require_expense_account",
    )
    def onchange_expense_account(self):
        for line in self.line_ids:
            line.expense_account_id = False
            domain = []
            if line.account_id:
                domain = [
                    ("employee_id", "=", self.employee_id.id),
                    ("state", "=", "open"),
                    ("type_id.account_ids", "in", [line.account_id.id]),
                    ("date_start", "<=", self.date),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", self.date),
                ]

                if line.require_expense_account:
                    expense_accounts = self.env["employee_expense_account"].search(
                        domain
                    )
                    if len(expense_accounts) > 0:
                        line.expense_account_id = expense_accounts[0]
