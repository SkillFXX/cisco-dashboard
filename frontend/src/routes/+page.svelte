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
	import OnboardingModal from "$lib/components/OnboardingModal.svelte";
	import NotificationsTab from "$lib/components/tabs/NotificationsTab.svelte";
	import AdminTab from "$lib/components/tabs/AdminTab.svelte";
	import MobileNav from "$lib/components/MobileNav.svelte";

	let activeTab = $state("dashboard");
	let isAddTaskOpen = $state(false);
	let taskPrefill = $state<{ subject?: string; event_type?: string } | null>(null);

	function openAddTask() {
		taskPrefill = null;
		isAddTaskOpen = true;
	}

	function openAddTaskForCourse(course: any) {
		const type = String(course?.type || "").toLowerCase();
		taskPrefill = { subject: course?.title || "", event_type: ["ds", "tp"].includes(type) ? type : "todo" };
		isAddTaskOpen = true;
	}
	let tasksRefreshTrigger = $state(0);
	// Incrémenté pour remonter les onglets et recharger leurs données (ex. fin de l'onboarding)
	let dataVersion = $state(0);

	// Onglets déjà visités : ils restent montés (masqués) pour un retour instantané, sans recharger
	let visited = $state<Set<string>>(new Set(["dashboard"]));
	let previousTab = "dashboard";

	$effect(() => {
		const tab = activeTab;
		if (previousTab === "settings" && tab !== "settings") {
			// Les services ont pu changer : repartir d'onglets neufs
			dataVersion += 1;
			visited = new Set([tab]);
		} else if (!visited.has(tab)) {
			visited = new Set([...visited, tab]);
		}
		previousTab = tab;
		window.scrollTo({ top: 0 });
	});

	const TABS = ["dashboard", "timetable", "grades", "tasks", "absences", "notifications", "settings", "admin"];

	onMount(async () => {
		// Raccourcis de l'application installée (?tab=tasks)
		const requested = new URLSearchParams(window.location.search).get("tab");
		if (requested && TABS.includes(requested)) activeTab = requested;
		await auth.init();
	});

	function handleTaskCreated() {
		tasksRefreshTrigger += 1;
		activeTab = "tasks";
	}
</script>

<svelte:head>
	<title>Cisco Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-app-bg text-zinc-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
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
			<MobileNav bind:activeTab />

			<!-- Main Area with Top Header -->
			<div class="flex-1 flex flex-col min-w-0 bg-app-bg">
				<TopHeader
					{activeTab}
					onOpenAddTask={openAddTask}
				/>

				<main class="flex-1 p-4 md:p-6 pb-24 md:pb-6 max-w-7xl w-full mx-auto">
					{#key dataVersion}
						{#if visited.has("dashboard")}
							<div class="tab-pane" class:hidden={activeTab !== "dashboard"}>
								<DashboardTab
									{tasksRefreshTrigger}
									onOpenAddTask={openAddTask}
									onNavigate={(tab: string) => (activeTab = tab)}
									onAddTaskForCourse={openAddTaskForCourse}
								/>
							</div>
						{/if}
						{#if visited.has("grades")}
							<div class="tab-pane" class:hidden={activeTab !== "grades"}><GradesTab /></div>
						{/if}
						{#if visited.has("timetable")}
							<div class="tab-pane" class:hidden={activeTab !== "timetable"}><TimetableTab onAddTaskForCourse={openAddTaskForCourse} /></div>
						{/if}
						{#if visited.has("tasks")}
							<div class="tab-pane" class:hidden={activeTab !== "tasks"}>
								<TasksTab {tasksRefreshTrigger} onOpenAddTask={openAddTask} />
							</div>
						{/if}
						{#if visited.has("absences")}
							<div class="tab-pane" class:hidden={activeTab !== "absences"}><AbsencesTab /></div>
						{/if}
						{#if visited.has("notifications")}
							<div class="tab-pane" class:hidden={activeTab !== "notifications"}><NotificationsTab /></div>
						{/if}
						{#if visited.has("settings")}
							<div class="tab-pane" class:hidden={activeTab !== "settings"}><SettingsTab /></div>
						{/if}
						{#if visited.has("admin") && auth.user?.is_admin}
							<div class="tab-pane" class:hidden={activeTab !== "admin"}><AdminTab /></div>
						{/if}
					{/key}
				</main>
			</div>
		</div>

		<!-- Modal d'ajout de DS & Évaluations -->
		<TaskModal
			bind:open={isAddTaskOpen}
			prefill={taskPrefill}
			onTaskCreated={handleTaskCreated}
		/>

		<!-- Assistant d'accueil pas à pas (Onboarding) -->
		<OnboardingModal
			bind:open={auth.isOnboardingOpen}
			onComplete={() => {
				tasksRefreshTrigger += 1;
				dataVersion += 1;
			}}
		/>
	{/if}
</div>
