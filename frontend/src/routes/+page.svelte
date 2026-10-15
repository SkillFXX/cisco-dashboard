<script lang="ts">
	import { onMount } from "svelte";
	import { auth } from "$lib/stores/auth.svelte";
	import Navbar from "$lib/components/Navbar.svelte";
	import TaskModal from "$lib/components/TaskModal.svelte";

	// Tabs
	import DashboardTab from "$lib/components/tabs/DashboardTab.svelte";
	import GradesTab from "$lib/components/tabs/GradesTab.svelte";
	import TimetableTab from "$lib/components/tabs/TimetableTab.svelte";
	import TasksTab from "$lib/components/tabs/TasksTab.svelte";
	import AbsencesTab from "$lib/components/tabs/AbsencesTab.svelte";
	import SettingsTab from "$lib/components/tabs/SettingsTab.svelte";
	import AuthView from "$lib/components/AuthView.svelte";

	let activeTab = $state("dashboard");
	let isAddTaskOpen = $state(false);

	onMount(async () => {
		await auth.init();
	});

	function handleTaskCreated() {
		// When a task/DS is created, switch to tasks or refresh
		activeTab = "tasks";
	}
</script>

<svelte:head>
	<title>Cisco - Panel Étudiant BUT R&T</title>
</svelte:head>

<div class="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
	{#if auth.isLoading}
		<div class="min-h-screen flex items-center justify-center">
			<div class="w-8 h-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin"></div>
		</div>
	{:else if !auth.isAuthenticated}
		<AuthView />
	{:else}
		<Navbar
			bind:activeTab
			onOpenAddTask={() => (isAddTaskOpen = true)}
		/>

		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			{#if activeTab === "dashboard"}
				<DashboardTab
					onOpenAddTask={() => (isAddTaskOpen = true)}
					onNavigate={(tab: string) => (activeTab = tab)}
				/>
			{:else if activeTab === "grades"}
				<GradesTab />
			{:else if activeTab === "timetable"}
				<TimetableTab />
			{:else if activeTab === "tasks"}
				<TasksTab onOpenAddTask={() => (isAddTaskOpen = true)} />
			{:else if activeTab === "absences"}
				<AbsencesTab />
			{:else if activeTab === "settings"}
				<SettingsTab />
			{/if}
		</main>

		<!-- Modal d'ajout de DS & Évaluations -->
		<TaskModal
			bind:open={isAddTaskOpen}
			onTaskCreated={handleTaskCreated}
		/>
	{/if}
</div>
