# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class MixinEmployeeDocument(models.AbstractModel):
    _name = "mixin.employee_document"
    _inherit = [
        "mixin.decorator",
    ]
    _description = "Mixin for Document With Employee Information"

    _search_by_employee = False
    _search_by_employee_xpath = "//field[last()]"

    @ssi_decorator.insert_on_search_view()
    def _employee_document_insert_search_element(self, view_arch):
        if self._search_by_employee:
            view_arch = self._add_view_element(
                view_arch=view_arch,
                qweb_template_xml_id="ssi_employee_document_mixin.employee_document_search",
                xpath=self._search_by_employee_xpath,
                position="after",
            )
        return view_arch

    @api.model
    def _default_employee_id(self):
        employees = self.env.user.employee_ids
        if len(employees) > 0:
            return employees[0].id

    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        default=lambda self: self._default_employee_id(),
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    department_id = fields.Many2one(
        string="Department",
        comodel_name="hr.department",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    manager_id = fields.Many2one(
        string="Manager",
        comodel_name="hr.employee",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    job_id = fields.Many2one(
        string="Job Position",
        comodel_name="hr.job",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    employee_partner_id = fields.Many2one(
        string="Employee Partner",
        related="employee_id.address_home_id",
        compute_sudo=True,
        store=False,
    )

    @api.onchange(
        "employee_id",
    )
    def onchange_department_id(self):
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id

    @api.onchange(
        "employee_id",
    )
    def onchange_manager_id(self):
        self.manager_id = False
        if self.employee_id:
            self.manager_id = self.employee_id.parent_id

    @api.onchange(
        "employee_id",
    )
    def onchange_job_id(self):
        self.job_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id
