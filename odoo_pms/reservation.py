
class Reservation(object):
    def __init__(self, ctx):
        self.odoo = ctx.odoo

    def get_stages(self, states=None):
        domain = [("stage_type", "=", "reservation")]
        if states:
            domain += [("name", "in", states)]

        return self.odoo.env["pms.stage"].search_read(domain, fields=["name"])

    def get_reservations(self, limit=10, states=None, order=None, no_public=False):
        domain = []
        if states:
            domain += [("stage_id", "in", [o["id"] for o in self.get_stages(states)])]

        if no_public:
            domain += [("user_id.name", "!=", "Public")]

        reservation_ids = self.odoo.env["pms.reservation"].search_read(
            domain,
            limit=limit,
            fields=[
                "guesty_id",
                "property_id",
                "stage_id",
                "sale_order_id",
                "user_id",
                "create_date"
            ],
            order=order or "id asc"
        )

        for reservation_id in reservation_ids:
            yield reservation_id
