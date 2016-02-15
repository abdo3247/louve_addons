# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Average Consumption Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from datetime import datetime as dt
from datetime import timedelta as td


HISTORY_RANGE = [
        # ('days', 'Days'),
        ('weeks', 'Week'),
        # ('months', 'Month'),
        ]


class ProductProduct(models.Model):
    _inherit = "product.product"

# Column section
    product_history_ids = fields.One2many(
        comodel_name='product.history', inverse_name='product_id',
        string='History')

# Private section
    @api.multi
    def _compute_qtys(self, states=('done',)):
        domain = [('state', 'in', states)] + self._get_domain_dates()
        for product in self:
            domain_product = domain + [('product_id', '=', product.id)]
            res = {
                'purchase_qty': 0,
                'view_qty': 0,
                'sale_qty': 0,
                'inventory_qty': 0,
                'procurement_qty': 0,
                'production_qty': 0,
                'transit_qty': 0,
                'total_qty': 0, }
            move_pool = self.env['stock.move']

            for field, usage, sign in (
                    ('purchase_qty', 'supplier', 1),
                    ('sale_qty', 'customer', 1),
                    ('inventory_qty', 'inventory', 1),
                    ('procurement_qty', 'procurement', 1),
                    ('production_qty', 'production', 1),
                    ('transit_qty', 'transit', 1),
                    ):
                moves = move_pool.read_group(domain_product + [
                    ('location_id.usage', '=', usage),
                    ('location_dest_id.usage', '=', 'internal'),
                ], ['product_qty'], [])
                for move in moves:
                    res[field] = sign * (move['product_qty'] or 0)
                    res['total_qty'] += sign * (move['product_qty'] or 0)
                moves = move_pool.read_group(domain_product + [
                    ('location_dest_id.usage', '=', usage),
                    ('location_id.usage', '=', 'internal'),
                ], ['product_qty'], [])
                for move in moves:
                    res[field] -= sign * (move['product_qty'] or 0)
                    res['total_qty'] -= sign * (move['product_qty'] or 0)
            return res

# Action section
#     @api.model
#     def run_product_history_day(self):
#         # This method is called by the cron task
#         products = self.env['product.product'].search([
#             '|', ('active', '=', True),
#             ('active', '=', False)])
#         products._compute_history('days')

    @api.model
    def run_product_history_week(self):
        # This method is called by the cron task
        products = self.env['product.product'].search([
            '|', ('active', '=', True),
            ('active', '=', False)])
        products._compute_history('weeks')

    # @api.model
    # def run_product_history_month(self):
    #     # This method is called by the cron task
    #     products = self.env['product.product'].search([
    #         '|', ('active', '=', True),
    #         ('active', '=', False)])
    #     products._compute_history('months')

    @api.one
    def action_compute_history(self):
        # dummy button function
        # TODO: erase!
        # self._compute_history('months')
        self.product_history_ids.unlink()
        self._compute_history('weeks')
        # self._compute_history('days')

    @api.multi
    def _compute_history(self):
        now = dt.now()
        current_date = dt.strftime(now, "%Y-%m-%d")

        for product in self:
            if product.product_history_ids:
            if history_range == "months":
                delta = rd(months=1)
            elif history_range == "weeks":
                delta = rd(weeks=1)
            else:
                delta = rd(days=1)
                self.env.cr.execute(
                    """SELECT to_date, end_qty FROM product_history
                    WHERE product_id=%s ORDER BY "id" DESC LIMIT 1"""
                    % (product.id))
                last_record = self.env.cr.fetchone()
                last_date = last_record and last_record[0] or None
                last_qty = last_record and last_record[1] or None
            else:
                self.env.cr.execute(
                    """SELECT date FROM stock_move
                    WHERE product_id=%s ORDER BY "date" LIMIT 1"""
                    % (product.id))
                last_date = self.env.cr.fetchone()[0]
                last_date = dt.strftime(dt.strptime(
                    last_date, "%Y-%m-%d %X"), "%Y-%m-%d")
                if history_range == "months":
                    from_date = date(
                        from_date.year, from_date.month, 1)
                elif history_range == "weeks":
                    from_date = from_date - td(days=from_date.weekday())
                last_qty = 0
            while last_date < current_date:
                new_from_date = dt.strftime(dt.strptime(
                        last_date, "%Y-%m-%d") + td(
                        seconds=1), "%Y-%m-%d %X")
                new_last_date = dt.strftime(dt.strptime(
                        last_date, "%Y-%m-%d") + td(days=1), "%Y-%m-%d")
                res = product.with_context({
                    'from_date': new_from_date,
                    'to_date': new_last_date})._compute_qtys()
                res2 = product.with_context({
                    'to_date': new_last_date,
                    })._product_available()[product.id]
                res3 = product.with_context({
                    'to_date': new_last_date})._compute_qtys()
                vals = {
                    'product_id': product.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'location_id': self.env['stock.location'].search([])[0].id,
                    'from_date': new_from_date,
                    'to_date': new_last_date,
                    'purchase_qty': res['purchase_qty'],
                    'sale_qty': res['sale_qty'],
                    'loss_qty': res['inventory_qty'],
                    'start_qty': last_qty,
                    'end_qty': res3['total_qty'],
                    'virtual_qty': res3['total_qty'] +
                    res2['incoming_qty'] - res2['outgoing_qty'],
                    'incoming_qty': res2['incoming_qty'],
                    'outgoing_qty': res2['outgoing_qty'],
                    'history_range': history_range,
                    }
                self.env['product.history'].create(vals)
                last_date = new_last_date
                last_qty = res3['total_qty']

