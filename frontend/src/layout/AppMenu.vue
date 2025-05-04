<script setup>
import { ref } from 'vue';

import AppMenuItem from './AppMenuItem.vue';

const model = ref([
    {
        label: 'Home',
        items: [{ label: 'Dashboard', icon: 'material-symbols:empty-dashboard-outline', to: '/' }]
    },
    {
        label: 'Menu',
        items: [
            { label: 'แผนที่นั่ง', icon: 'material-symbols:airline-seat-recline-normal', to: '/uikit/formlayout' },
            { label: 'รายชื่อบัณฑิต', icon: 'material-symbols:patient-list-outline', to: '/uikit/crud01' },
            { label: 'รายชื่อที่ผ่านเข้าประตู', icon: 'material-symbols:person-check-outline-rounded', to: '/uikit/table' },
            { label: 'Logs', icon: 'material-symbols:file-present-outline-sharp', to: '/uikit/logs' },
            { label: 'Chart', icon: 'material-symbols:grouped-bar-chart-rounded', to: '/uikit/charts' },
            { label: 'Test', icon: 'svg-spinners:ring-resize', to: '/uikit/test' }
        ]
    }
    // {
    //     label: 'Pages',
    //     icon: 'pi pi-fw pi-briefcase',
    //     to: '/pages',
    //     items: [
    //         {
    //             label: 'Auth',
    //             icon: 'pi pi-fw pi-user',
    //             items: [
    //                 {
    //                     label: 'Login',
    //                     icon: 'pi pi-fw pi-sign-in',
    //                     to: '/auth/login'
    //                 }
    //             ]
    //         }
    //     ]
    // }
]);
</script>

<template>
    <div>
        <ul class="layout-menu">
            <template v-for="(item, i) in model">
                <app-menu-item v-if="!item.separator" :item="item" :index="i" :key="`item-${i}`"></app-menu-item>
                <li v-if="item.separator" class="menu-separator" :key="`separator-${i}`"></li>
            </template>
        </ul>
    </div>
</template>

<style lang="scss" scoped></style>
