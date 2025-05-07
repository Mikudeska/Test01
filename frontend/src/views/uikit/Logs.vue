<!-- Logs.vue -->
<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();
const logs = ref([]);
let refreshInterval = null;

// รีเซ็ตข้อมูล
const confirmResetDialog1 = ref(false);
const confirmResetDialog2 = ref(false);
const resetKeyword = ref('');

const confirmResetdatabase = () => {
    confirmResetDialog1.value = true;
};

const handleResetStep1 = () => {
    confirmResetDialog1.value = false;
    confirmResetDialog2.value = true;
};

const handleResetStep2 = async () => {
    if (resetKeyword.value.toUpperCase() !== 'RESET') {
        toast.add({
            severity: 'error',
            summary: 'ยืนยันไม่สำเร็จ',
            detail: 'กรุณาพิมพ์คำว่า "RESET" ให้ถูกต้อง',
            life: 3000
        });
        resetKeyword.value = '';
        return;
    }
    try {
        await axios.post('http://localhost:8000/api/resetlog/');
        await fetchLogs();
        toast.add({
            severity: 'success',
            summary: 'รีเซ็ตสำเร็จ',
            detail: 'ลบข้อมูลทั้งหมดเรียบร้อย',
            life: 5000
        });
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'รีเซ็ตล้มเหลว',
            detail: error.response?.data?.error || 'เกิดข้อผิดพลาด',
            life: 5000
        });
    } finally {
        confirmResetDialog2.value = false;
        resetKeyword.value = '';
    }
};

// ฟังก์ชันแปลงรายละเอียด Log
const parsedDetails = (details) => {
    const labels = {
        name: 'ชื่อ',
        nisit: 'รหัสนิสิต',
        degree: 'ปริญญา',
        seat: 'ที่นั่ง',
        verified: 'สถานะ',
        rfid: 'RFID'
    };

    return details.split('|').map((part) => {
        const [field, old, newVal] = part.split('::');

        // แปลงค่า verified เป็นตัวเลข
        const processValue = (value, field) => {
            if (field === 'verified') {
                const statusMap = {
                    ยังไม่รายงานตัว: 0,
                    รายงานตัวแล้ว: 1,
                    อยู่ในห้องพิธี: 2
                };
                return statusMap[value] ?? value;
            }
            return value;
        };

        return {
            field,
            label: labels[field] || field,
            old: processValue(old, field),
            new: processValue(newVal, field)
        };
    });
};

// ฟังก์ชันจัดการไอคอน verified
const getVerifiedIcon = (value) => {
    const icons = {
        0: 'rivet-icons:close-circle-solid',
        1: 'rivet-icons:check-circle-solid',
        2: 'rivet-icons:exclamation-mark-circle-solid'
    };
    return icons[value] || 'mdi:alert-circle-outline';
};

// ฟังก์ชันจัดการสี verified
const getVerifiedColor = (value) => {
    // ตรวจสอบชนิดข้อมูลของ value
    const status = Number(value);
    if (status === 1) return 'text-green-500';
    if (status === 0) return 'text-red-500';
    if (status === 2) return 'text-yellow-500'; // เปลี่ยนจาก yellow-300 เป็น yellow-500
    return 'text-gray-400';
};

const fetchLogs = async () => {
    try {
        let allLogs = [];
        let nextUrl = 'http://127.0.0.1:8000/api/logs/';

        while (nextUrl) {
            const response = await axios.get(nextUrl);
            const data = response.data;

            // ตรวจสอบโครงสร้างข้อมูล
            const pageLogs = data.results || data;

            // กรอง null และเพิ่มข้อมูล
            allLogs.push(...pageLogs.filter((log) => log !== null));

            // อัพเดท URL ถัดไป (รองรับทั้ง relative และ absolute URL)
            nextUrl = data.next?.replace('http://localhost:8000', '') || data.next;
        }

        logs.value = allLogs;
    } catch (error) {
        console.error('Error fetching logs:', error);
        toast.add({
            severity: 'error',
            summary: 'เกิดข้อผิดพลาด',
            detail: 'ดึงข้อมูลไม่สำเร็จ',
            life: 3000
        });
    }
};

onMounted(() => {
    fetchLogs();
    refreshInterval = setInterval(fetchLogs, 5000);
});

onUnmounted(() => {
    clearInterval(refreshInterval);
});
</script>

<template>
    <div class="flex flex-col h-full card">
        <Toolbar class="mb-6">
            <template #start>
                <Button severity="secondary" class="mr-2" @click="confirmResetdatabase" rounded raised>
                    <Icon icon="lucide:database-backup" />
                    <span>รีเซ็ตประวัติ</span>
                </Button>
            </template>
        </Toolbar>
        <DataTable
            :value="logs"
            :paginator="true"
            :rows="10"
            :filters="filters"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            :rowsPerPageOptions="[5, 10, 25]"
            currentPageReportTemplate="จาก   {first} ถึง {last} ของทั้งหมด {totalRecords} คน"
            scrollable
            scrollHeight="flex"
            class="h-full"
            :pt="{
                root: { class: 'flex-1 flex flex-col' },
                loadingOverlay: { class: 'flex-1' },
                wrapper: { class: 'flex-1 flex flex-col' },
                table: { class: 'min-w-[800px]' }
            }"
        >
            <!-- คอลัมน์รายการ -->
            <Column field="id" header="รายการ" style="min-width: 50px">
                <template #body="{ data }">
                    <span v-if="data?.id" class="font-semibold">
                        {{ data.id }}
                    </span>
                </template>
            </Column>

            <!-- คอลัมน์วันที่ -->
            <Column field="timestamp" header="วันที่" style="min-width: 100px">
                <template #body="{ data }">
                    <template v-if="data?.timestamp">
                        {{
                            new Date(data.timestamp).toLocaleDateString('th-TH', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit'
                            })
                        }}
                    </template>
                    <span v-else class="text-gray-400">N/A</span>
                </template>
            </Column>

            <!-- คอลัมน์เวลา -->
            <Column field="timestamp" header="เวลา" style="min-width: 100px">
                <template #body="{ data }">
                    <template v-if="data?.timestamp">
                        {{
                            new Date(data.timestamp).toLocaleTimeString('th-TH', {
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            })
                        }}
                    </template>
                    <span v-else class="text-gray-400">N/A</span>
                </template>
            </Column>

            <!-- คอลัมน์การกระทำ -->
            <Column field="action" header="การกระทำ" style="min-width: 100px">
                <template #body="{ data }">
                    <Tag
                        v-if="data?.action"
                        :value="data.action"
                        :severity="
                            {
                                Add: 'success',
                                Edit: 'info',
                                Delete: 'danger',
                                Import: 'warning',
                                Export: 'help',
                                Reset: 'danger'
                            }[data.action]
                        "
                    />
                </template>
            </Column>

            <Column field="" header="ผู้ใช้" style="min-width: 100px"></Column>

            <!-- คอลัมน์รายละเอียด -->
            <Column field="details" header="รายละเอียด" style="min-width: 500px">
                <template #body="{ data }">
                    <div v-if="data?.details" class="flex flex-wrap items-center gap-2">
                        <!-- แสดง ID -->
                        <span v-if="data.record_id" class="font-semibold text-blue-600">[ID: {{ data.record_id }}]</span>

                        <!-- แสดงการเปลี่ยนแปลงทั้งหมดในบรรทัดเดียว -->
                        <template v-for="(item, index) in parsedDetails(data.details)" :key="index">
                            <div class="flex items-center gap-1">
                                <!-- กรณีแก้ไข verified -->
                                <template v-if="item.field === 'verified'">
                                    <span class="shrink-0">{{ item.label }}:</span>
                                    <span :class="getVerifiedColor(item.old)">
                                        <Icon :icon="getVerifiedIcon(item.old)" />
                                    </span>
                                    <Icon v-if="item.new !== null && item.new !== undefined" icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                    <span v-if="item.new !== null && item.new !== undefined" :class="getVerifiedColor(item.new)">
                                        <Icon :icon="getVerifiedIcon(item.new)" />
                                    </span>
                                </template>
                                <!-- กรณีแก้ไขฟิลด์อื่น -->
                                <template v-else>
                                    <span class="font-medium">{{ item.label }}:</span>
                                    <span class="text-red-500 line-through">{{ item.old }}</span>
                                    <Icon v-if="item.new !== undefined" icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                    <span v-if="item.new !== undefined" class="text-green-500">{{ item.new }}</span>
                                </template>
                            </div>
                            <!-- เพิ่มเส้นคั่น -->
                            <span v-if="index < parsedDetails(data.details).length - 1 && item.new !== undefined">|</span>
                        </template>
                    </div>
                </template>
            </Column>

            <template #empty>
                <div class="py-6 text-center text-gray-400">ไม่พบข้อมูล Logs</div>
            </template>
        </DataTable>

        <!-- Dialog ยืนยันขั้นที่ 1 -->
        <Dialog v-model:visible="confirmResetDialog1" header="ยืนยันการรีเซ็ต" :modal="true" :style="{ width: '500px' }">
            <div class="flex items-center gap-4 p-4">
                <Icon icon="bi:exclamation-triangle-fill" class="text-yellow-300" />
                <div>
                    <h3 class="mb-2 text-lg font-bold">คุณแน่ใจที่จะรีเซ็ตประวัติทั้งหมด?</h3>
                    <p class="text-black">การกระทำนี้จะลบข้อมูลทุกรายการและไม่สามารถกู้คืนได้</p>
                </div>
            </div>
            <template #footer>
                <Button label="ยกเลิก" icon="pi pi-times" @click="confirmResetDialog1 = false" severity="secondary" text />
                <Button label="ดำเนินการต่อ" icon="pi pi-arrow-right" @click="handleResetStep1" severity="danger" />
            </template>
        </Dialog>

        <!-- Dialog ยืนยันขั้นที่ 2 -->
        <Dialog v-model:visible="confirmResetDialog2" header="ยืนยันขั้นสุดท้าย" :modal="true" :style="{ width: '500px' }">
            <div class="flex flex-col gap-4 p-4">
                <div class="flex items-center gap-4">
                    <Icon icon="teenyicons:shield-solid" class="text-3xl text-red-500" />
                    <h3 class="text-lg font-bold">กรุณาพิมพ์คำว่า "RESET"</h3>
                </div>

                <InputText v-model="resetKeyword" placeholder="พิมพ์คำว่า RESET ที่นี่" class="w-full" autocomplete="off" @keyup.enter="handleResetStep2" />
            </div>
            <template #footer>
                <Button label="ยกเลิก" icon="pi pi-times" @click="confirmResetDialog2 = false" severity="secondary" text />
                <Button label="ยืนยันรีเซ็ต" icon="pi pi-check" @click="handleResetStep2" :disabled="resetKeyword.toUpperCase() !== 'RESET'" severity="danger" />
            </template>
        </Dialog>
    </div>
</template>

<style scoped>
.card {
    height: calc(100vh - 150px); /* ลดความสูงเพื่อให้พอดีกับ paginator */
}
</style>
