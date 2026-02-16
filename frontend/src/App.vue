<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container app-container">
      <a class="d-flex align-items-center" :href="portfolioUrl" aria-label="Open SparkUp portfolio">
        <img :src="sparkupLogo" alt="SparkUp" width="34" height="34" class="me-3" />
      </a>

      <span class="navbar-brand navbar-title mx-auto mx-lg-0">Autonomous Spacecraft</span>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#mainNavbar"
        aria-controls="mainNavbar"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="mainNavbar">
        <ul class="navbar-nav ms-auto mb-2 mb-lg-0 gap-1">
          <li class="nav-item">
            <RouterLink class="nav-link" to="/" active-class="active" exact-active-class="active">Home</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/launch" active-class="active" exact-active-class="active">Launch</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/dashboard" active-class="active" exact-active-class="active">Dashboard</RouterLink>
          </li>
          <li class="nav-item">
            <a class="nav-link nav-link--icon" :href="repoUrl" target="_blank" rel="noopener" aria-label="GitHub">
              <img :src="githubIcon" alt="GitHub" class="nav-icon" width="34" height="34" />
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>

  <main class="page">
    <div class="container app-container py-4">
      <div class="content-surface">
        <RouterView />
      </div>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container text-center">
      <div class="footer-line">
        Handcrafted with
        <img
          src="data:image/svg+xml,%3c?xml%20version='1.0'%20encoding='utf-8'?%3e%3csvg%20width='18px'%20height='18px'%20viewBox='0%200%2024%2024'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20d='M12%205.881C12.981%204.729%2014.484%204%2016.05%204C18.822%204%2021%206.178%2021%208.95C21%2012.3492%2017.945%2015.1195%2013.3164%2019.3167L13.305%2019.327L12%2020.515L10.695%2019.336L10.6595%2019.3037C6.04437%2015.1098%203%2012.3433%203%208.95C3%206.178%205.178%204%207.95%204C9.516%204%2011.019%204.729%2012%205.881Z'%20fill='%237c6cff'%20/%3e%3c/svg%3e"
          alt="heart"
          class="mx-1 footer-heart"
        />
        in Lyon, France
      </div>
      <div class="footer-copy mt-1">All rights reserved © 2026</div>
    </div>
  </footer>
</template>

<script setup>
const staticBase = import.meta.env.VITE_SPARKUP_STATIC_BASE || "https://static.sparkup.dev";
const sparkupLogo = `${staticBase}/images/sparkup.svg`;
const githubIcon = `${staticBase}/icons/github.svg`;
const portfolioUrl = import.meta.env.VITE_SPARKUP_PORTFOLIO_URL || "https://www.sparkup.dev";
const repoUrl = import.meta.env.VITE_REPO_URL || "https://github.com/sparkup/autonomous-spacecraft-rl";
</script>
