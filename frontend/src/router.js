import { createRouter, createWebHistory } from "vue-router";
import HomePage from "./pages/HomePage.vue";
import RocketPage from "./pages/RocketPage.vue";
import DashboardPage from "./pages/DashboardPage.vue";

const routes = [
  { path: "/", component: HomePage },
  { path: "/launch", component: RocketPage },
  { path: "/dashboard", component: DashboardPage },

  // Backward compatibility URLs
  { path: "/how-it-works", redirect: "/" },
  { path: "/api", redirect: "/" },
  { path: "/rocket", redirect: "/launch" },
  { path: "/interface", redirect: "/launch" }
];

export default createRouter({
  history: createWebHistory(),
  routes
});
