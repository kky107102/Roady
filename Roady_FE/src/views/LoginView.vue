<script setup lang="ts">
import LoginCard from '@/components/auth/LoginCard.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
</script>

<template>
  <AuthLayout content-labelledby="login-title">
    <LoginCard />
  </AuthLayout>
</template>
