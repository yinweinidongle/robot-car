<template>
  <div class="app">
    <MapComponent />
  </div>
</template>

<script>
import MapComponent from './components/MapComponent.vue'

export default {
  name: 'App',
  components: {
    MapComponent
  }
}
</script>

<style>
.app {
  width: 100%;
  height: 100vh;
}
</style> 