from rest_framework import serializers
from .models import Person, Log

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'

    def validate_nisit(self, value):
        if Person.objects.filter(nisit=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("รหัสนิสิตนี้มีอยู่แล้ว")
        return value
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # แปลงข้อมูลให้เป็นรูปแบบที่ JSON serializable
        data['_original'] = {
            'id': instance.id,
            'name': instance.name,
            'nisit': instance.nisit,
            'degree': instance.degree,
            'seat': instance.seat,
            'verified': instance.verified,
            'rfid': instance.rfid
        }
        return data

class LogSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # กำหนด format ชัดเจน
    
    class Meta:
        model = Log
        fields = '__all__'