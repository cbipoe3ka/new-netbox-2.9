from extras.plugins import PluginConfig

class PaymentConfig(PluginConfig):
    name = 'payment'
    verbose_name = 'Payment'
    description = 'netbox plugin for collect payment information about rent equipment'
    version = '1.0'
    author = 'Ovsyannikov Alexandr'
    author_email = 'ovs.alexandr@gmail.com'
    required_settings = []
    default_settings = {
        'loud': True
    }
    base_url = 'payment',
    caching_config = {}

config = PaymentConfig