<script lang="ts">
	import { onMount } from "svelte";
	import { auth } from "$lib/stores/auth.svelte";
	import Sidebar from "$lib/components/Sidebar.svelte";
	import TopHeader from "$lib/components/TopHeader.svelte";
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
		activeTab = "tasks";
	}
</script>

<svelte:head>
	<title>Cisco - Panel Étudiant BUT R&T</title>
</svelte:head>

<div class="min-h-screen bg-[#080A0F] text-zinc-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
	{#if auth.isLoading}
		<div class="min-h-screen flex items-center justify-center">
			<div class="w-8 h-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin"></div>
		</div>
	{:else if !auth.isAuthenticated}
		<AuthView />
	{:else}
		<div class="flex min-h-screen">
			<!-- Fixed Left Sidebar matching mockup -->
			<Sidebar bind:activeTab />

			<!-- Main Area with Top Header -->
			<div class="flex-1 flex flex-col min-w-0 bg-[#080A0F]">
				<TopHeader
					{activeTab}
					onOpenAddTask={() => (isAddTaskOpen = true)}
				/>

				<main class="flex-1 p-6 max-w-7xl w-full mx-auto overflow-y-auto">
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
			</div>
		</div>

		<!-- Modal d'ajout de DS & Évaluations -->
		<TaskModal
			bind:open={isAddTaskOpen}
			onTaskCreated={handleTaskCreated}
		/>
	{/if}
</div>
