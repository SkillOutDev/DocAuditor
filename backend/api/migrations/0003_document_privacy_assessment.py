from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_document_risk_assessment"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="privacy_assessment",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
