# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EmployeeExpenseAccount(models.Model):
    _inherit = "employee_expense_account"

    reimbursement_line_ids = fields.One2many(
        comodel_name="hr.reimbursement_line",
        inverse_name="expense_account_id",
        string="All Reimbursements",
    )

    @api.depends(
        "reimbursement_line_ids",
        "reimbursement_line_ids.reimbursement_id",
        "reimbursement_line_ids.reimbursement_id.state",
    )
    def _compute_valid_reimbursement_line_ids(self):
        for record in self:
            result = record.reimbursement_line_ids.filtered(
                lambda x: x.reimbursement_id.state
                not in ("reject", "cancel", "terminate")
            )
            record.valid_reimbursement_line_ids = result

    valid_reimbursement_line_ids = fields.One2many(
        string="Reimbursements",
        comodel_name="hr.reimbursement_line",
        compute="_compute_valid_reimbursement_line_ids",
        compute_sudo=True,
    )

    @api.depends(
        "reimbursement_line_ids",
        "reimbursement_line_ids.price_subtotal",
        "reimbursement_line_ids.reimbursement_id.state",
    )
    def _compute_reimbursement(self):
        for record in self:
            result = 0.0
            for line in record.reimbursement_line_ids.filtered(
                lambda x: x.reimbursement_id.state
                not in ("reject", "cancel", "terminate")
            ):
                result += line.price_subtotal
            record.amount_reimbursement = result
            record._compute_amount()

    amount_reimbursement = fields.Monetary(
        compute="_compute_reimbursement",
        store=True,
        string="Reimbursement",
        compute_sudo=True,
    )

    def _get_expense_fields(self):
        _super = super(EmployeeExpenseAccount, self)
        res = _super._get_expense_fields()
        res.append("amount_reimbursement")
        return res
