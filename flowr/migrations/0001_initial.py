# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DCCGraph',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('data_content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'DCC Graph',
            },
        ),
        migrations.CreateModel(
            name='Flow',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=25)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FlowNodeData',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('rule_label', models.CharField(max_length=80)),
            ],
            options={
                'verbose_name': 'Flow Node Data',
                'verbose_name_plural': 'Flow Node Data',
            },
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('children', models.ManyToManyField(related_name='child_nodes', to='flowr.Node')),
                ('graph', models.ForeignKey(to='flowr.DCCGraph')),
                ('parents', models.ManyToManyField(related_name='parent_nodes', to='flowr.Node')),
            ],
        ),
        migrations.CreateModel(
            name='RuleSet',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=80)),
                ('root_rule_label', models.CharField(max_length=80)),
            ],
            options={
                'verbose_name': 'Rule Set',
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('current_node', models.ForeignKey(to='flowr.Node')),
                ('flow', models.ForeignKey(to='flowr.Flow')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='flownodedata',
            name='node',
            field=models.OneToOneField(to='flowr.Node'),
        ),
        migrations.AddField(
            model_name='flow',
            name='rule_set',
            field=models.ForeignKey(to='flowr.RuleSet'),
        ),
        migrations.AddField(
            model_name='flow',
            name='state_graph',
            field=models.ForeignKey(to='flowr.DCCGraph'),
        ),
        migrations.AddField(
            model_name='dccgraph',
            name='root',
            field=models.ForeignKey(to='flowr.Node', blank=True, null=True),
        ),
    ]
