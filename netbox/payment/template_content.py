from extras.plugins import PluginTemplateExtension


from .models import Payment


class SitePaymentCount(PluginTemplateExtension):
    model = 'dcim.site'

    def right_page(self):
        pass