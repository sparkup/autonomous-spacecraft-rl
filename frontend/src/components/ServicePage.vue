<template>
  <section class="page-copy">
    <h1>{{ title }}</h1>
    <p class="text-muted">{{ description }}</p>

    <div class="service-card mt-4">
      <p class="mb-2"><strong>Service URL</strong></p>
      <code>{{ href }}</code>
      <div class="mt-3 d-flex gap-2 flex-wrap">
        <a class="btn btn-primary" :href="href" target="_blank" rel="noopener">Open in new tab</a>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  href: { type: String, required: true }
});
</script>
