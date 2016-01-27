# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('moment_id', models.CharField(max_length=100)),
                ('provider_name', models.CharField(max_length=50)),
                ('album_pk', models.IntegerField()),
                ('feeditem_pk', models.IntegerField()),
                ('url', models.TextField()),
                ('views', models.IntegerField(default=0)),
                ('downloaded', models.BooleanField(default=False)),
                ('revoked', models.BooleanField(default=False)),
            ],
        ),
    ]
