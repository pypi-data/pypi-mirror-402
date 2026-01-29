from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Domain
from .settings import domain_settings
from .signals import after_add_domain, before_add_domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        exclude = ['tenant', 'instrument_id']

    def validate_provider(self, value: str):
        if value in domain_settings.get_supported_providers():
            return value
        raise ValidationError(f"Provider '{value}' is not supported")

    def validate_hostname(self, value: str):
        if domain_settings.BLOCKED_DOMAINS and value.endswith(tuple(domain_settings.BLOCKED_DOMAINS)):
            raise ValidationError('This hostname is not allowed')
        return value

    def create(self, validated_data):
        before_add_domain.send(self.__class__, data=validated_data, **self.context)
        instance = super().create(validated_data)
        after_add_domain.send(self.__class__, instance=instance, **self.context)
        return instance
