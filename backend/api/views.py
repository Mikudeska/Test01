from django.http import HttpResponse
from .resources import PersonResource
from tablib import Dataset
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Person, Log
from .serializers import PersonSerializer, LogSerializer
from django.db import transaction, connection
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import urllib.parse
import os, io, json

class ResetDatabase(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. บันทึกจำนวนข้อมูลก่อนลบ (Option)
                total_records = Person.objects.count()
                
                # 2. ลบข้อมูลทั้งหมด
                Person.objects.all().delete()
                
                # 3. รีเซ็ต AUTO_INCREMENT (MySQL/MariaDB)
                reset_auto_increment = False
                if 'mysql' in connection.settings_dict['ENGINE']:
                    cursor = connection.cursor()
                    table_name = Person._meta.db_table
                    cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
                    reset_auto_increment = True
                
                # 4. บันทึก Log
                log_details = (
                    f"รีเซ็ตฐานข้อมูล | ลบข้อมูลทั้งหมด {total_records} รายการ"
                )
                
                Log.objects.create(
                    action='Reset',
                    model='Database',
                    details=log_details,
                    record_id=None
                )
                
                return Response(
                    {'success': 'รีเซ็ตฐานข้อมูลสำเร็จ'}, 
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            # บันทึก Log กรณี error
            Log.objects.create(
                action='Reset',
                model='Database',
                details=f"รีเซ็ตล้มเหลว: {str(e)}",
                record_id=None,
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ResetLog(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. บันทึกจำนวนข้อมูลก่อนลบ (Option)
                total_records = Log.objects.count()
                
                # 2. ลบข้อมูลทั้งหมด
                Log.objects.all().delete()
                
                # 3. รีเซ็ต AUTO_INCREMENT (MySQL/MariaDB)
                reset_auto_increment = False
                if 'mysql' in connection.settings_dict['ENGINE']:
                    cursor = connection.cursor()
                    table_name = Log._meta.db_table
                    cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
                    reset_auto_increment = True
                
                # 4. บันทึก Log
                log_details = (
                    f"รีเซ็ตประวัติ | ลบข้อมูลทั้งหมด {total_records} รายการ"
                )
                
                Log.objects.create(
                    action='Reset',
                    model='Database',
                    details=log_details,
                    record_id=None
                )   
                
                return Response(
                    {'success': 'รีเซ็ตประวัติสำเร็จ'}, 
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            # บันทึก Log กรณี error
            Log.objects.create(
                action='Reset',
                model='Database',
                details=f"รีเซ็ตล้มเหลว: {str(e)}",
                record_id=None,
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExportPDF(APIView):
    def get(self, request):
        try:
            # ตั้งค่า Font ไทย
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'THSarabunNew.ttf')
            pdfmetrics.registerFont(TTFont('THSarabun', FONT_PATH))

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            p.setFont('THSarabun', 14)

            # เขียนหัวตาราง
            p.drawString(50, 800, "ลำดับ")
            p.drawString(150, 800, "ชื่อ-นามสกุล")
            p.drawString(300, 800, "รหัสนิสิต")
            p.drawString(400, 800, "สถานะรายงานตัว")

            # ดึงข้อมูล
            persons = Person.objects.all().order_by('seat')
            y_position = 780  # ตำแหน่งเริ่มต้น

            for i, person in enumerate(persons, start=1):
                p.drawString(50, y_position, f"{i:04d}")
                p.drawString(150, y_position, person.name)
                p.drawString(300, y_position, person.nisit)
                p.drawString(400, y_position, str(person.verified))
                y_position -= 20  # เลื่อนบรรทัด

                # ขึ้นหน้าใหม่หากข้อมูลเต็มหน้า
                if y_position < 50:
                    p.showPage()
                    y_position = 800
                    p.setFont('THSarabun', 14)

            p.save()
            buffer.seek(0)

            # สร้าง HTTP Response
            response = HttpResponse(
                buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = 'attachment; filename="graduates.pdf"'
            return response

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ExportData(APIView):
    def get(self, request, format_type):
        resource = PersonResource()
        dataset = resource.export()
        response = None  # กำหนดค่าเริ่มต้น

        try:
            format_type = format_type.lower()  # แปลงเป็นตัวเล็กทั้งหมด

            if format_type == 'xlsx':
                response = HttpResponse(
                    dataset.xlsx,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                filename = urllib.parse.quote('รายชื่อบัณฑิต.xlsx')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            elif format_type == 'csv':
                response = HttpResponse(dataset.csv, content_type='text/csv; charset=utf-8-sig')
                filename = urllib.parse.quote('รายชื่อบัณฑิต.csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            else:
                return Response(
                    {'error': 'รูปแบบไฟล์ไม่ถูกต้อง'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            Log.objects.create(
                action='Export',
                model='Person',
                details=f"โหลดไฟล์เป็น {format_type}"
            )
            return response

        except Exception as e:
            return Response(
                {'error': 'Internal Server Error'}, 
                status=500
            )

class ImportData(APIView):
    def post(self, request):
        file = request.FILES['file']
        dataset = Dataset()
        resource = PersonResource()

        try:
            # อ่านไฟล์
            if file.name.endswith('.xlsx'):
                dataset.load(file.read(), format='xlsx')
            elif file.name.endswith('.csv'):
                dataset.load(file.read().decode('utf-8-sig'), format='csv')

            # ตรวจสอบข้อมูล
            if len(dataset) == 0:
                raise ValueError("ไฟล์ที่อัปโหลดว่างเปล่า")

            # นำเข้าข้อมูล
            result = resource.import_data(dataset, dry_run=False, raise_errors=True)
            
            # แก้ไขการนับจำนวนรายการ
            imported_count = (
                result.totals.get('new', 0)    # ข้อมูลใหม่
                + result.totals.get('update', 0)  # ข้อมูลที่อัปเดต
            )

            # บันทึก Log
            Log.objects.create(
                action='Import',
                model='Person',
                details=f"นำเข้าฐานข้อมูล {imported_count} รายการ ( ใหม่ {result.totals.get('new', 0)} อัปเดต {result.totals.get('update', 0)} )",
                record_id=None
            )

            return Response(
                {'success': f'นำเข้าข้อมูลสำเร็จ {imported_count} รายการ'}, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            Log.objects.create(
                action='Import',
                model='Person',
                details=f"นำเข้าข้อมูลล้มเหลว: {str(e)}",
                record_id=None
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class StatsView(APIView):
    def get(self, request):
        total = Person.objects.count()  # นับจำนวนทั้งหมด
        checked_in = Person.objects.filter(verified=0).count()  # verified = 0
        in_checkin_room = Person.objects.filter(verified=1).count()  # verified = 1
        in_graduation_room = Person.objects.filter(verified=2).count()  # verified = 2

        stats = {
            'total': total,
            'checked_in': checked_in,
            'in_checkin_room': in_checkin_room,
            'in_graduation_room': in_graduation_room
        }
        return Response(stats, status=status.HTTP_200_OK)

class PersonList(APIView):
    def get(self, request):
        persons = Person.objects.all()
        serializer = PersonSerializer(persons, many=True)
        # ตรวจสอบข้อมูลก่อนส่ง response
        safe_data = []
        for item in serializer.data:
            safe_item = {
                k: v for k, v in item.items() 
                if isinstance(v, (str, int, float, bool, type(None)))
            }
            safe_data.append(safe_item)
        return Response(safe_data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()  # เก็บ instance ที่สร้าง
            Log.objects.create(
                action='Add',
                model='Person',
                details=f"เพิ่มข้อมูล: {instance.name}",
                record_id=instance.id
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonSerializer(person, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # ดึงข้อมูลก่อนลบเพื่อบันทึก Log
                persons = Person.objects.filter(id__in=ids)
                for person in persons:
                    Log.objects.create(
                        action='Delete',
                        model='Person',
                        details=f"ลบข้อมูลแบบกลุ่ม: {person.name} (ID: {person.id})",
                        record_id=person.id
                    )
                persons.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PersonDetail(APIView):
    def get(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonSerializer(person)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
            # บันทึก Log ก่อนลบ
            Log.objects.create(
                action='Delete',
                model='Person',
                details=f"ลบข้อมูลของ {person.name}",
                record_id=person.id
            )
            person.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
            original_data = {
                'name': person.name,
                'nisit': person.nisit,
                'degree': person.degree,
                'seat': person.seat,
                'verified': person.verified,
                'rfid': person.rfid
            }
        
            serializer = PersonSerializer(person, data=request.data)
            if serializer.is_valid():
                serializer.save()
                person.refresh_from_db()  # โหลดข้อมูลใหม่จาก DB
            
                # ตรวจสอบฟิลด์ที่เปลี่ยนแปลง
                changes = []
                for field in ['name', 'degree', 'seat', 'verified', 'rfid']:
                    old_val = original_data[field]
                    new_val = getattr(person, field)
                    if old_val != new_val:
                        changes.append(f"{field}::{old_val}::{new_val}")  # ใช้ :: เป็นตัวแบ่งข้อมูล
            
                # สร้างข้อความ Log
                log_message = " | ".join(changes)
            
                Log.objects.create(
                    action='Edit',
                    model='Person',
                    details=log_message, 
                    record_id=person.id
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
class RFIDSimulator(APIView):
    parser_classes = [JSONParser]
    
    def post(self, request):
        try:
            simulated_tags = request.data.get('tags', [])
            
            if not simulated_tags:
                return Response(
                    {'error': 'No tags provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            results = []
            for tag in simulated_tags:
                epc = tag.get('epc')
                if not epc:
                    continue

                try:
                    person = Person.objects.get(rfid=epc)
                    
                    # ตรวจสอบสถานะก่อนอัปเดต
                    if person.verified == 1:
                        results.append({
                            'epc': epc,
                            'name': person.name,
                            'message': 'แท็กนี้ถูกสแกนแล้ว',
                        })
                    else:
                        # อัปเดตสถานะเป็น 2 ถ้ายังไม่เคยสแกน
                        person.verified = 1
                        person.save()
                        results.append({
                            'epc': epc,
                            'name': person.name,
                            'message': 'อัปเดตสถานะสำเร็จ',
                        })
                        
                except Person.DoesNotExist:
                    results.append({
                        'epc': epc,
                        'message': 'ไม่พบข้อมูลแท็กนี้ในระบบ',
                        'name': None
                    })
            Log.objects.create(
                action='rfid_scan',
                model='Person',
                details=f"RFID: {epc} Status: {person.verified}"
            )
            return Response({'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogList(generics.ListAPIView):
    serializer_class = LogSerializer
    
    def get_queryset(self):
        # กรองข้อมูลที่อาจมี timestamp เป็น null
        return Log.objects.exclude(timestamp__isnull=True).order_by('-timestamp')