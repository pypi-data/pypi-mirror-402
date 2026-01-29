# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrExpenseType(models.Model):
    _name = "hr.expense_type"
    _inherit = "hr.expense_type"

    reimbursement_journal_id = fields.Many2one(
        string="Reimbursement Journal",
        comodel_name="account.journal",
    )
    reimbursement_account_id = fields.Many2one(
        string="Reimbursement Account",
        comodel_name="account.account",
    )
