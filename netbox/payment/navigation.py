from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices


menu_items = (

    PluginMenuItem(
        link='plugins:payment:payment_list',
        link_text='Payments list',
        permissions=['payment.view_payment'],
        buttons= (

            PluginMenuButton(
                link='plugins:payment:payment_add',
                permissions=['payment.add_payment'],
                title='Add payment',
                icon_class='fa fa-plus',
                color=ButtonColorChoices.GREEN,
            ),
        )
    ),
)