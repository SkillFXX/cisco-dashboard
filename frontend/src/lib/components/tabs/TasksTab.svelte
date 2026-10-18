<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import TaskModal from "../TaskModal.svelte";
	import { api } from "$lib/api";
	import { formatDateFr } from "$lib/utils";
	import {
		ListTodo,
		PlusCircle,
		CheckCircle2,
		Circle,
		Trash2,
		Calendar,
		RefreshCw,
		ChevronDown,
		ChevronRight,
		ExternalLink,
		X,
		Clock,
		BookOpen,
		MapPin,
		Check,
		Pencil
	} from "lucide-svelte";

	let {
		onOpenAddTask,
		tasksRefreshTrigger = 0
	}: {
		onOpenAddTask?: () => void;
		tasksRefreshTrigger?: number;
	} = $props();

	let lastTasksTrigger = $state(0);
	$effect(() => {
		if (tasksRefreshTrigger > lastTasksTrigger) {
			lastTasksTrigger = tasksRefreshTrigger;
			loadAllData(false);
		}
	});

	let personalTasks = $state<any[]>([]);
	let moodleAssignments = $state<any[]>([]);
	let timetableEvents = $state<any[]>([]);
	let completedExternalIds = $state<Set<string>>(new Set());

	let isLoading = $state(true);
	let error = $state("");
	let activeCategory = $state<string>("ALL"); // ALL, DS, DM, TP, AUTRES

	// Accordéon pour les 3 catégories
	let isTodoOpen = $state(true);
	let isLongTermOpen = $state(true);
	let isDoneOpen = $state(false);

	// Sidebar tiroir pour le détail d'un devoir
	let selectedTask = $state<any>(null);

	// Modal d'édition d'une tâche personnelle
	let isEditModalOpen = $state(false);
	let taskToEdit = $state<any>(null);

	function computeDaysLeft(isoDateStr: string): number {
		const now = new Date();
		now.setHours(0, 0, 0, 0);
		const dueDate = new Date(isoDateStr);
		const dueDateMidnight = new Date(dueDate);
		dueDateMidnight.setHours(0, 0, 0, 0);
		return Math.round((dueDateMidnight.getTime() - now.getTime()) / (1000 * 3600 * 24));
	}

	function formatFullDate(isoDateStr: string): string {
		if (!isoDateStr) return "--";
		try {
			const d = new Date(isoDateStr);
			return d.toLocaleDateString("fr-FR", {
				weekday: "long",
				day: "numeric",
				month: "long",
				year: "numeric"
			});
		} catch {
			return isoDateStr;
		}
	}

	function formatTime(isoDateStr: string): string {
		if (!isoDateStr) return "";
		try {
			const d = new Date(isoDateStr);
			const hours = d.getHours().toString().padStart(2, "0");
			const minutes = d.getMinutes().toString().padStart(2, "0");
			return `${hours}:${minutes}`;
		} catch {
			return "";
		}
	}

	async function loadAllData(forceRefresh = false) {
		isLoading = true;
		error = "";
		try {
			// Charger le cache local des tâches externes cochées
			let localCompleted: string[] = [];
			if (typeof window !== "undefined") {
				try {
					localCompleted = JSON.parse(localStorage.getItem("cisco_completed_tasks") || "[]");
				} catch {
					localCompleted = [];
				}
			}

			const [pTasks, mData, tData, serverCompleted] = await Promise.all([
				api.getTasks(),
				api.getMoodleAssignments(forceRefresh).catch(() => ({ assignments: [] })),
				api.getTimetableWeek(forceRefresh).catch(() => ({ all_events: [] })),
				api.getCompletedExternalTasks().catch(() => [])
			]);

			personalTasks = pTasks || [];
			moodleAssignments = mData.assignments || [];
			timetableEvents = tData.all_events || [];

			// Fusion des identifiants cochés (serveur + local)
			const mergedSet = new Set<string>([...localCompleted, ...(serverCompleted || [])]);
			completedExternalIds = mergedSet;
			if (typeof window !== "undefined") {
				localStorage.setItem("cisco_completed_tasks", JSON.stringify(Array.from(mergedSet)));
			}
		} catch (err: any) {
			error = err.message || "Erreur lors du chargement des devoirs.";
		} finally {
			isLoading = false;
		}
	}

	async function toggleTask(task: any) {
		const isCurrentlyDone = task.status === "done";
		const newStatus = isCurrentlyDone ? "todo" : "done";

		// Mise à jour optimiste immédiate
		task.status = newStatus;
		if (selectedTask && selectedTask.id === task.id) {
			selectedTask.status = newStatus;
		}

		if (!task.is_personal) {
			const nextSet = new Set(completedExternalIds);
			if (newStatus === "done") {
				nextSet.add(task.id);
			} else {
				nextSet.delete(task.id);
			}
			completedExternalIds = nextSet;
			if (typeof window !== "undefined") {
				localStorage.setItem("cisco_completed_tasks", JSON.stringify(Array.from(nextSet)));
			}
		}

		try {
			await api.toggleItemStatus(task.id, newStatus);
		} catch (err) {
			console.error("Erreur toggle task:", err);
		}
	}

	async function deleteTask(id: number) {
		if (!confirm("Voulez-vous supprimer cette épreuve / tâche ?")) return;
		try {
			await api.deleteTask(id);
			personalTasks = personalTasks.filter((t) => t.id !== id);
			if (selectedTask?.id === `personal-${id}`) {
				selectedTask = null;
			}
		} catch (err) {
			console.error(err);
		}
	}

	onMount(() => {
		loadAllData();

		const handleKeyDown = (e: KeyboardEvent) => {
			if (e.key === "Escape") {
				selectedTask = null;
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	});

	// Liste unifiée de tous les devoirs
	let allUnifiedItems = $derived(() => {
		// 1. Tâches personnelles
		const personal = personalTasks.map((t) => {
			const daysLeft = computeDaysLeft(t.due_date);
			let cat = "AUTRES";
			if (t.event_type === "ds") cat = "DS";
			else if (t.event_type === "dm") cat = "DM";
			else if (t.event_type === "tp") cat = "TP";

			return {
				id: `personal-${t.id}`,
				task_id: t.id,
				title: t.title,
				subject: t.subject || "Personnel",
				category: cat,
				due_date: t.due_date,
				days_left: daysLeft,
				status: t.status || "todo",
				description: t.description,
				is_personal: true,
				source: "personal"
			};
		});

		// 2. Moodle (automatiquement dans DM)
		const moodle = moodleAssignments.map((m) => {
			const itemId = `moodle-${m.id}`;
			const isDone = completedExternalIds.has(itemId);
			const daysLeft = m.days_left !== undefined ? m.days_left : computeDaysLeft(m.duedate);

			return {
				id: itemId,
				title: m.name,
				subject: m.course_name || "Moodle",
				category: "DM",
				due_date: m.duedate,
				days_left: daysLeft,
				status: isDone ? "done" : "todo",
				description: m.description,
				url: m.url,
				is_personal: false,
				source: "moodle"
			};
		});

		// 3. Timetable Calendrier (avec tag DS)
		const timetableDs = (timetableEvents || [])
			.filter((e) => e.type === "DS")
			.map((e) => {
				const itemId = `timetable-${e.id || e.dt_start}`;
				const isDone = completedExternalIds.has(itemId);
				const daysLeft = computeDaysLeft(e.dt_start || e.date);
				const rawRoom = (e.location || "").trim();
				const room = rawRoom ? (rawRoom.toLowerCase().startsWith("salle") ? rawRoom : `Salle ${rawRoom}`) : "Salle non précisée";

				return {
					id: itemId,
					title: e.title || "Contrôle DS",
					subject: "DS",
					category: "DS",
					due_date: e.dt_start || e.date,
					days_left: daysLeft,
					status: isDone ? "done" : "todo",
					description: room,
					is_personal: false,
					source: "timetable",
					start_time: e.start_time,
					end_time: e.end_time,
					location: room
				};
			});

		return [...personal, ...moodle, ...timetableDs];
	});

	// Filtrage par catégorie sélectionnée (Toutes, DS, DM, TP, Autres)
	let filteredItems = $derived(() => {
		const items = allUnifiedItems();
		if (activeCategory === "ALL") return items;
		return items.filter((i) => i.category === activeCategory);
	});

	// Répartition dans les 3 groupes
	let todoItems = $derived(() => {
		return filteredItems()
			.filter((i) => i.status !== "done" && i.days_left <= 30)
			.sort((a, b) => a.days_left - b.days_left);
	});

	let longTermItems = $derived(() => {
		return filteredItems()
			.filter((i) => i.status !== "done" && i.days_left > 30)
			.sort((a, b) => a.days_left - b.days_left);
	});

	let doneItems = $derived(() => {
		return filteredItems()
			.filter((i) => i.status === "done")
			.sort((a, b) => b.days_left - a.days_left);
	});
</script>

<div class="space-y-6 relative">
	<!-- En-tête de la page -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<ListTodo class="w-5 h-5 text-cyan-400" />
				<span>Devoirs</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Vos devoirs, travaux à rendre et devoirs surveillés.
			</p>
		</div>

		<div class="flex items-center gap-2">
			<button
				onclick={() => loadAllData(true)}
				disabled={isLoading}
				class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-white/[0.04] border border-app-border text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
			>
				<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
				<span>Actualiser</span>
			</button>
			<button
				onclick={() => {
					taskToEdit = null;
					isEditModalOpen = true;
				}}
				class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
			>
				<PlusCircle class="w-3.5 h-3.5" />
				<span>Ajouter un devoir</span>
			</button>
		</div>
	</div>

	<!-- Filtres de Catégories (DS / DM / TP / Autres) sans parenthèses -->
	<div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-app-border">
		{#each [
			{ id: 'ALL', label: 'Toutes les catégories' },
			{ id: 'DS', label: 'DS' },
			{ id: 'DM', label: 'DM' },
			{ id: 'TP', label: 'TP' },
			{ id: 'AUTRES', label: 'Autres' }
		] as cat}
			<button
				onclick={() => (activeCategory = cat.id)}
				class="px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {activeCategory === cat.id
					? 'bg-white/[0.08] text-white shadow-xs'
					: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
			>
				{cat.label}
			</button>
		{/each}
	</div>

	{#if isLoading && personalTasks.length === 0 && moodleAssignments.length === 0}
		<div class="space-y-6">
			<!-- Section À faire Skeleton -->
			<div class="space-y-3">
				<div class="flex items-center justify-between p-2">
					<div class="flex items-center gap-2">
						<Skeleton class="w-4 h-4 rounded-md" />
						<Skeleton class="h-4 w-20" />
						<Skeleton class="h-4 w-6 rounded-full" />
					</div>
					<Skeleton class="h-3 w-32" />
				</div>

				<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-white/5">
					{#each Array(4) as _}
						<div class="p-3.5 flex items-center justify-between gap-3">
							<div class="flex items-center gap-3.5 flex-1 min-w-0">
								<Skeleton class="w-5 h-5 rounded-full shrink-0" />
								<div class="space-y-1.5 flex-1">
									<Skeleton class="h-3.5 w-36" />
									<Skeleton class="h-2.5 w-48" />
								</div>
							</div>
							<div class="flex items-center gap-6 shrink-0">
								<Skeleton class="h-5 w-12 rounded-full" />
								<Skeleton class="h-3 w-24" />
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Section Dans longtemps Skeleton -->
			<div class="space-y-3">
				<div class="flex items-center justify-between p-2">
					<div class="flex items-center gap-2">
						<Skeleton class="w-4 h-4 rounded-md" />
						<Skeleton class="h-4 w-28" />
						<Skeleton class="h-4 w-6 rounded-full" />
					</div>
					<Skeleton class="h-3 w-32" />
				</div>

				<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-white/5">
					{#each Array(2) as _}
						<div class="p-3.5 flex items-center justify-between gap-3">
							<div class="flex items-center gap-3.5 flex-1 min-w-0">
								<Skeleton class="w-5 h-5 rounded-full shrink-0" />
								<div class="space-y-1.5 flex-1">
									<Skeleton class="h-3.5 w-32" />
									<Skeleton class="h-2.5 w-44" />
								</div>
							</div>
							<div class="flex items-center gap-6 shrink-0">
								<Skeleton class="h-5 w-12 rounded-full" />
								<Skeleton class="h-3 w-24" />
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
			{error}
		</div>
	{:else}
		<div class="space-y-6">
			<!-- Section 1 : À faire (dans le mois) -->
			<div class="space-y-2">
				<button
					type="button"
					onclick={() => (isTodoOpen = !isTodoOpen)}
					class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02] text-left transition-colors cursor-pointer"
				>
					<div class="flex items-center gap-2">
						{#if isTodoOpen}
							<ChevronDown class="w-4 h-4 text-zinc-400" />
						{:else}
							<ChevronRight class="w-4 h-4 text-zinc-400" />
						{/if}
						<span class="text-sm font-bold text-white">À faire</span>
						<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-cyan-600 text-white">
							{todoItems().length}
						</span>
					</div>
					<span class="text-xs text-zinc-500">Échéance d'ici 30 jours</span>
				</button>

				{#if isTodoOpen}
					{#if todoItems().length === 0}
						<div class="py-8 text-center border border-dashed border-app-border rounded-xl bg-app-card/40 text-zinc-500 text-xs">
							Aucun devoir à faire dans les 30 prochains jours.
						</div>
					{:else}
						<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-white/5">
							{#each todoItems() as item}
								<!-- Ligne du tableau -->
								<div
									role="button"
									tabindex="0"
									onclick={() => (selectedTask = item)}
									onkeydown={(e) => { if (e.key === 'Enter') selectedTask = item; }}
									class="flex items-center justify-between p-3.5 hover:bg-white/[0.02] transition-colors cursor-pointer gap-3 text-left"
								>
									<!-- Checkbox + Matière & Titre -->
									<div class="flex items-center gap-3.5 min-w-0 flex-1">
										<button
											type="button"
											onclick={(e) => {
												e.stopPropagation();
												toggleTask(item);
											}}
											class="text-zinc-500 hover:text-cyan-400 transition-colors cursor-pointer shrink-0"
											title="Marquer comme fait"
										>
											<Circle class="w-5 h-5" />
										</button>

										<div class="min-w-0 flex-1">
											<!-- Titre du devoir mis en évidence -->
											<div class="flex items-center gap-2">
												<span class="font-bold text-xs text-white truncate">
													{item.title}
												</span>
												{#if item.source === "moodle"}
													<span class="text-[10px] text-cyan-400 font-medium shrink-0">Moodle</span>
												{:else if item.source === "timetable"}
													<span class="text-[10px] text-rose-400 font-medium shrink-0">Calendrier</span>
												{/if}
											</div>
											<!-- Salle ou consignes sous le titre -->
											{#if item.description}
												<p class="text-xs text-zinc-400 truncate mt-0.5">
													{item.description}
												</p>
											{/if}
										</div>
									</div>

									<!-- Catégorie (au milieu) : badge rond en couleur pleine -->
									<div class="shrink-0 hidden sm:flex items-center justify-center">
										{#if item.category === 'DS'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-rose-600 text-white">
												DS
											</span>
										{:else if item.category === 'DM'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-cyan-600 text-white">
												DM
											</span>
										{:else if item.category === 'TP'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-purple-600 text-white">
												TP
											</span>
										{:else}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-zinc-100">
												Autres
											</span>
										{/if}
									</div>

									<!-- Date et délai (à droite) -->
									<div class="flex flex-col items-end shrink-0 text-right">
										<div class="text-xs font-semibold">
											{#if item.days_left < 0}
												<span class="text-rose-400">En retard ({Math.abs(item.days_left)} j)</span>
											{:else if item.days_left === 0}
												<span class="text-amber-300">Aujourd'hui</span>
											{:else if item.days_left === 1}
												<span class="text-amber-200">Demain</span>
											{:else if item.days_left <= 5}
												<span class="text-zinc-200">Dans <span class="text-white font-bold">{item.days_left}</span> jours</span>
											{:else}
												<span class="text-zinc-400">Dans <span class="text-white font-bold">{item.days_left}</span> jours</span>
											{/if}
										</div>
										<span class="text-[11px] text-zinc-500 mt-0.5">
											{formatDateFr(item.due_date)}
										</span>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				{/if}
			</div>

			<!-- Section 2 : Dans longtemps (> 1 mois) -->
			<div class="space-y-2">
				<button
					type="button"
					onclick={() => (isLongTermOpen = !isLongTermOpen)}
					class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02] text-left transition-colors cursor-pointer"
				>
					<div class="flex items-center gap-2">
						{#if isLongTermOpen}
							<ChevronDown class="w-4 h-4 text-zinc-400" />
						{:else}
							<ChevronRight class="w-4 h-4 text-zinc-400" />
						{/if}
						<span class="text-sm font-bold text-white">Dans longtemps</span>
						<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-zinc-700 text-white">
							{longTermItems().length}
						</span>
					</div>
					<span class="text-xs text-zinc-500">Échéance à plus d'1 mois</span>
				</button>

				{#if isLongTermOpen}
					{#if longTermItems().length === 0}
						<div class="py-8 text-center border border-dashed border-app-border rounded-xl bg-app-card/40 text-zinc-500 text-xs">
							Aucun devoir prévu à plus d'un mois.
						</div>
					{:else}
						<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-white/5">
							{#each longTermItems() as item}
								<!-- Ligne du tableau -->
								<div
									role="button"
									tabindex="0"
									onclick={() => (selectedTask = item)}
									onkeydown={(e) => { if (e.key === 'Enter') selectedTask = item; }}
									class="flex items-center justify-between p-3.5 hover:bg-white/[0.02] transition-colors cursor-pointer gap-3 text-left"
								>
									<!-- Checkbox + Matière & Titre -->
									<div class="flex items-center gap-3.5 min-w-0 flex-1">
										<button
											type="button"
											onclick={(e) => {
												e.stopPropagation();
												toggleTask(item);
											}}
											class="text-zinc-500 hover:text-cyan-400 transition-colors cursor-pointer shrink-0"
											title="Marquer comme fait"
										>
											<Circle class="w-5 h-5" />
										</button>

										<div class="min-w-0 flex-1">
											<div class="flex items-center gap-2">
												<span class="font-bold text-xs text-white truncate">
													{item.title}
												</span>
												{#if item.source === "moodle"}
													<span class="text-[10px] text-cyan-400 font-medium shrink-0">Moodle</span>
												{:else if item.source === "timetable"}
													<span class="text-[10px] text-rose-400 font-medium shrink-0">Calendrier</span>
												{/if}
											</div>
											{#if item.description}
												<p class="text-xs text-zinc-400 truncate mt-0.5">
													{item.description}
												</p>
											{/if}
										</div>
									</div>

									<!-- Catégorie (au milieu) -->
									<div class="shrink-0 hidden sm:flex items-center justify-center">
										{#if item.category === 'DS'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-rose-600 text-white">
												DS
											</span>
										{:else if item.category === 'DM'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-cyan-600 text-white">
												DM
											</span>
										{:else if item.category === 'TP'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-purple-600 text-white">
												TP
											</span>
										{:else}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-zinc-100">
												Autres
											</span>
										{/if}
									</div>

									<!-- Date et délai (à droite) -->
									<div class="flex flex-col items-end shrink-0 text-right">
										<div class="text-xs font-semibold text-zinc-400">
											Dans <span class="text-white font-bold">{item.days_left}</span> jours
										</div>
										<span class="text-[11px] text-zinc-500 mt-0.5">
											{formatDateFr(item.due_date)}
										</span>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				{/if}
			</div>

			<!-- Section 3 : Fait / Terminés -->
			<div class="space-y-2">
				<button
					type="button"
					onclick={() => (isDoneOpen = !isDoneOpen)}
					class="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02] text-left transition-colors cursor-pointer"
				>
					<div class="flex items-center gap-2">
						{#if isDoneOpen}
							<ChevronDown class="w-4 h-4 text-zinc-400" />
						{:else}
							<ChevronRight class="w-4 h-4 text-zinc-400" />
						{/if}
						<span class="text-sm font-bold text-white">Fait</span>
						<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-zinc-700 text-white">
							{doneItems().length}
						</span>
					</div>
					<span class="text-xs text-zinc-500">Devoirs et épreuves validés</span>
				</button>

				{#if isDoneOpen}
					{#if doneItems().length === 0}
						<div class="py-8 text-center border border-dashed border-app-border rounded-xl bg-app-card/40 text-zinc-500 text-xs">
							Aucun devoir marqué comme fait.
						</div>
					{:else}
						<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-white/5 opacity-70">
							{#each doneItems() as item}
								<!-- Ligne du tableau -->
								<div
									role="button"
									tabindex="0"
									onclick={() => (selectedTask = item)}
									onkeydown={(e) => { if (e.key === 'Enter') selectedTask = item; }}
									class="flex items-center justify-between p-3.5 hover:bg-white/[0.02] transition-colors cursor-pointer gap-3 text-left"
								>
									<!-- Checkbox + Matière & Titre -->
									<div class="flex items-center gap-3.5 min-w-0 flex-1">
										<button
											type="button"
											onclick={(e) => {
												e.stopPropagation();
												toggleTask(item);
											}}
											class="text-emerald-400 hover:text-zinc-400 transition-colors cursor-pointer shrink-0"
											title="Marquer comme non fait"
										>
											<CheckCircle2 class="w-5 h-5" />
										</button>

										<div class="min-w-0 flex-1">
											<div class="flex items-center gap-2">
												<span class="font-bold text-xs text-zinc-400 line-through truncate">
													{item.title}
												</span>
												{#if item.source === "moodle"}
													<span class="text-[10px] text-zinc-500 font-medium shrink-0">Moodle</span>
												{:else if item.source === "timetable"}
													<span class="text-[10px] text-zinc-500 font-medium shrink-0">Calendrier</span>
												{/if}
											</div>
											{#if item.description}
												<p class="text-xs text-zinc-500 line-through truncate mt-0.5">
													{item.description}
												</p>
											{/if}
										</div>
									</div>

									<!-- Catégorie (au milieu) -->
									<div class="shrink-0 hidden sm:flex items-center justify-center">
										{#if item.category === 'DS'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-800 text-zinc-400">
												DS
											</span>
										{:else if item.category === 'DM'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-800 text-zinc-400">
												DM
											</span>
										{:else if item.category === 'TP'}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-800 text-zinc-400">
												TP
											</span>
										{:else}
											<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-800 text-zinc-400">
												Autres
											</span>
										{/if}
									</div>

									<!-- Date et délai (à droite) -->
									<div class="flex flex-col items-end shrink-0 text-right">
										<span class="text-xs font-semibold text-emerald-400">
											Terminé
										</span>
										<span class="text-[11px] text-zinc-500 mt-0.5">
											{formatDateFr(item.due_date)}
										</span>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				{/if}
			</div>
		</div>
	{/if}

	<!-- Sidebar latérale à droite (Détail du devoir) -->
	{#if selectedTask}
		<div class="fixed inset-0 z-50 flex justify-end">
			<!-- Fond sombre cliquable pour fermer -->
			<button
				type="button"
				aria-label="Fermer"
				onclick={() => (selectedTask = null)}
				class="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity cursor-pointer border-none"
			></button>

			<!-- Panneau latéral coulissant -->
			<div
				class="relative w-full max-w-md h-full bg-app-card border-l border-app-border shadow-2xl flex flex-col z-10 overflow-y-auto"
			>
				<!-- En-tête du volet -->
				<div class="flex items-center justify-between p-5 border-b border-app-border">
					<div>
						<h2 class="text-base font-bold text-white">Détail du devoir</h2>
						<p class="text-xs text-zinc-400 mt-0.5">{selectedTask.subject}</p>
					</div>
					<button
						type="button"
						onclick={() => (selectedTask = null)}
						class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors cursor-pointer"
						aria-label="Fermer"
					>
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- Corps du volet -->
				<div class="p-6 space-y-6 flex-1">
					<!-- Badge catégorie et titre -->
					<div class="space-y-3">
						<div class="flex items-center gap-2">
							{#if selectedTask.category === 'DS'}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-rose-600 text-white">
									DS
								</span>
							{:else if selectedTask.category === 'DM'}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-cyan-600 text-white">
									DM
								</span>
							{:else if selectedTask.category === 'TP'}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-purple-600 text-white">
									TP
								</span>
							{:else}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-zinc-700 text-zinc-100">
									Autres
								</span>
							{/if}

							{#if selectedTask.source === "moodle"}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-medium bg-zinc-800 text-cyan-400">
									Moodle
								</span>
							{:else if selectedTask.source === "timetable"}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-medium bg-zinc-800 text-rose-400">
									Calendrier
								</span>
							{/if}
						</div>

						<h3 class="text-lg font-bold text-white leading-snug">
							{selectedTask.title}
						</h3>
					</div>

					<!-- Statut actuel et bouton de bascule -->
					<div class="p-4 rounded-xl bg-app-surface border border-app-border flex items-center justify-between">
						<div>
							<div class="text-[11px] text-zinc-400 uppercase font-semibold">Statut actuel</div>
							<div class="text-xs font-bold mt-0.5 {selectedTask.status === 'done' ? 'text-emerald-400' : 'text-amber-400'}">
								{selectedTask.status === 'done' ? 'Terminé' : 'À faire'}
							</div>
						</div>
						<button
							type="button"
							onclick={() => toggleTask(selectedTask)}
							class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer {selectedTask.status === 'done' ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-emerald-600 hover:bg-emerald-500 text-white'}"
						>
							{#if selectedTask.status === 'done'}
								Marquer à faire
							{:else}
								Marquer comme fait
							{/if}
						</button>
					</div>

					<!-- Carte Date et Délai -->
					<div class="p-4 rounded-xl bg-app-surface border border-app-border space-y-3">
						<div class="flex items-center justify-between text-xs">
							<span class="text-zinc-400 flex items-center gap-1.5">
								<Calendar class="w-4 h-4 text-cyan-400" />
								<span>Date limite</span>
							</span>
							<span class="font-bold text-white capitalize">
								{formatFullDate(selectedTask.due_date)}
							</span>
						</div>

						{#if formatTime(selectedTask.due_date)}
							<div class="flex items-center justify-between text-xs pt-2 border-t border-white/5">
								<span class="text-zinc-400 flex items-center gap-1.5">
									<Clock class="w-4 h-4 text-cyan-400" />
									<span>Heure d'échéance</span>
								</span>
								<span class="font-bold text-white">
									{formatTime(selectedTask.due_date)}
								</span>
							</div>
						{/if}

						<div class="flex items-center justify-between text-xs pt-2 border-t border-white/5">
							<span class="text-zinc-400">Temps restant</span>
							<span class="font-bold text-white">
								{#if selectedTask.status === 'done'}
									<span class="text-emerald-400">Validé</span>
								{:else if selectedTask.days_left < 0}
									<span class="text-rose-400">En retard de {Math.abs(selectedTask.days_left)} jours</span>
								{:else if selectedTask.days_left === 0}
									<span class="text-amber-300">Aujourd'hui</span>
								{:else if selectedTask.days_left === 1}
									<span class="text-amber-200">Demain</span>
								{:else}
									Dans {selectedTask.days_left} jours
								{/if}
							</span>
						</div>
					</div>

					<!-- Consignes / Description -->
					{#if selectedTask.description}
						<div class="space-y-1.5">
							<h4 class="text-xs font-bold text-zinc-300 uppercase tracking-wider">
								{selectedTask.source === "timetable" ? "Salle" : "Consignes / Détails"}
							</h4>
							<div class="p-4 rounded-xl bg-app-surface border border-app-border text-xs text-zinc-300 whitespace-pre-line leading-relaxed max-h-60 overflow-y-auto">
								{selectedTask.description}
							</div>
						</div>
					{/if}

					<!-- Lien direct Moodle -->
					{#if selectedTask.source === "moodle"}
						<div class="space-y-2 pt-2">
							<a
								href={selectedTask.url || "https://moodle-but.iutbeziers.fr/moodle"}
								target="_blank"
								rel="noopener noreferrer"
								class="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-all shadow-xs cursor-pointer"
							>
								<ExternalLink class="w-4 h-4" />
								<span>Ouvrir sur Moodle</span>
							</a>
							<p class="text-[11px] text-zinc-500 text-center">
								Ouvre directement la page de dépôt ou le cours correspondant sur Moodle.
							</p>
						</div>
					{/if}

					<!-- Modification et Suppression si tâche personnelle -->
					{#if selectedTask.is_personal}
						<div class="pt-4 border-t border-app-border space-y-2">
							<button
								type="button"
								onclick={() => {
									taskToEdit = selectedTask;
									isEditModalOpen = true;
								}}
								class="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] text-white font-semibold text-xs transition-all border border-app-border cursor-pointer"
							>
								<Pencil class="w-4 h-4 text-cyan-400" />
								<span>Modifier ce devoir</span>
							</button>

							<button
								type="button"
								onclick={() => deleteTask(selectedTask.task_id)}
								class="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-xl hover:bg-red-600/10 text-zinc-400 hover:text-red-400 font-medium text-xs transition-all cursor-pointer"
							>
								<Trash2 class="w-4 h-4" />
								<span>Supprimer cette épreuve / tâche</span>
							</button>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<!-- Modal de modification de devoir personnel -->
	<TaskModal
		bind:open={isEditModalOpen}
		task={taskToEdit}
		onTaskSaved={() => {
			loadAllData(true);
			selectedTask = null;
		}}
	/>
</div>
