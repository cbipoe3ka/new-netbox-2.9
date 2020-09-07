from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dcim', '0104_correct_infiniband_types'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=70)),
                ('price', models.IntegerField()),
                ('period', models.CharField(default='monthly', max_length=50)),
                ('payment_date', models.DateField()),
                ('comments', models.TextField(blank=True)),
                ('devices', models.ManyToManyField(blank=True, to='dcim.Device')),
            ],
            options={
                'ordering': ['payment_date', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ContractFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=30)),
                ('document', models.FileField(upload_to='devicetype-images')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
