<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Badge from "../Badge.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { formatDateFr } from "$lib/utils";
	import {
		ListTodo,
		PlusCircle,
		CheckCircle2,
		Circle,
		Trash2,
		Calendar,
		RefreshCw
	} from "lucide-svelte";

	let {
		onOpenAddTask
	}: {
		onOpenAddTask?: () => void;
	} = $props();

	let tasks = $state<any[]>([]);
	let moodleAssignments = $state<any[]>([]);
	let isLoading = $state(true);
	let error = $state("");
	let filterType = $state<string>("ALL"); // ALL, TODO, DONE, DS, MOODLE

	async function loadAllData() {
		isLoading = true;
		error = "";
		try {
			const [personalList, moodleData] = await Promise.all([
				api.getTasks(),
				api.getMoodleAssignments().catch(() => ({ assignments: [] }))
			]);
			tasks = personalList;
			moodleAssignments = moodleData.assignments || [];
		} catch (err: any) {
			error = err.message || "Erreur lors du chargement des tâches.";
		} finally {
			isLoading = false;
		}
	}

	async function toggleStatus(task: any) {
		const newStatus = task.status === "done" ? "todo" : "done";
		try {
			await api.updateTask(task.id, { status: newStatus });
			task.status = newStatus;
		} catch (e) {
			console.error(e);
		}
	}

	async function deleteTask(id: number) {
		if (!confirm("Voulez-vous supprimer cette épreuve / tâche ?")) return;
		try {
			await api.deleteTask(id);
			tasks = tasks.filter((t) => t.id !== id);
		} catch (e) {
			console.error(e);
		}
	}

	onMount(() => {
		loadAllData();
	});

	let displayedItems = $derived(() => {
		// Personal tasks
		const now = new Date();
		now.setHours(0, 0, 0, 0);

		const personal = tasks.map((t) => {
			const dueDate = new Date(t.due_date);
			const dueDateMidnight = new Date(dueDate);
			dueDateMidnight.setHours(0, 0, 0, 0);
			const daysLeft = Math.round((dueDateMidnight.getTime() - now.getTime()) / (1000 * 3600 * 24));
			return {
				...t,
				is_personal: true,
				days_left: daysLeft
			};
		});

		// Moodle assignments (uniquement aujourd'hui et à venir)
		const moodle = moodleAssignments
			.filter((m) => m.days_left >= 0)
			.map((m) => ({
				id: `m-${m.id}`,
				title: m.name,
				subject: m.course_name,
				due_date: m.duedate,
				days_left: m.days_left,
				event_type: "dm",
				status: "todo",
				description: m.description,
				is_personal: false
			}));

		const all = [...personal, ...moodle];

		if (filterType === "TODO") return all.filter((i) => i.status === "todo" && i.days_left >= 0);
		if (filterType === "DONE") return all.filter((i) => i.status === "done");
		if (filterType === "DS") return all.filter((i) => i.event_type === "ds");
		if (filterType === "MOODLE") return all.filter((i) => !i.is_personal && i.days_left >= 0);

		// Vue par défaut : aujourd'hui et à venir
		return all
			.filter((i) => i.status === "done" || i.days_left >= 0)
			.sort((a, b) => a.days_left - b.days_left);
	});
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<ListTodo class="w-5 h-5 text-cyan-400" />
				<span>Devoirs, DM Moodle & Dates de DS</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Gérez l'ensemble de vos échéances : devoirs Moodle synchronisés et contrôles / DS ajoutés manuellement.
			</p>
		</div>

		<div class="flex items-center gap-2">
			<button
				onclick={loadAllData}
				disabled={isLoading}
				class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-white/[0.04] border border-app-border text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
			>
				<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
				<span>Actualiser</span>
			</button>
			{#if onOpenAddTask}
				<button
					onclick={onOpenAddTask}
					class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
				>
					<PlusCircle class="w-3.5 h-3.5" />
					<span>Ajouter un DS / Devoir</span>
				</button>
			{/if}
		</div>
	</div>

	<!-- Filters -->
	<div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-app-border">
		{#each [
			{ id: 'ALL', label: 'Toutes les échéances' },
			{ id: 'TODO', label: 'À faire' },
			{ id: 'DS', label: 'Contrôles (DS)' },
			{ id: 'MOODLE', label: 'Moodle' },
			{ id: 'DONE', label: 'Terminés' }
		] as f}
			<button
				onclick={() => (filterType = f.id)}
				class="px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {filterType === f.id
					? 'bg-white/[0.08] text-white shadow-xs'
					: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
			>
				{f.label}
			</button>
		{/each}
	</div>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center p-12 text-zinc-400">
			<RefreshCw class="w-7 h-7 animate-spin text-cyan-400 mb-3" />
			<p class="text-xs">Chargement des devoirs et contrôles programmés...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
			{error}
		</div>
	{:else}
		<div class="space-y-3">
			{#if displayedItems().length === 0}
				<Card class="text-center py-12 text-zinc-500 text-xs">
					Aucun devoir ou contrôle correspondant à ce filtre.
				</Card>
			{:else}
				{#each displayedItems() as item}
					<Card class="p-4 hover:border-zinc-700 {item.status === 'done' ? 'opacity-60' : ''}">
						<div class="flex items-start justify-between gap-4">
							<div class="flex items-start gap-3">
								{#if item.is_personal}
									<button
										onclick={() => toggleStatus(item)}
										class="mt-1 text-zinc-400 hover:text-cyan-400 transition-colors cursor-pointer"
										title={item.status === 'done' ? 'Marquer comme non fait' : 'Marquer comme fait'}
									>
										{#if item.status === 'done'}
											<CheckCircle2 class="w-5 h-5 text-emerald-400" />
										{:else}
											<Circle class="w-5 h-5" />
										{/if}
									</button>
								{:else}
									<div class="mt-1 w-5 h-5 rounded-full bg-amber-600/30 flex items-center justify-center shrink-0" title="Synchronisé depuis Moodle">
										<span class="w-2 h-2 rounded-full bg-amber-400"></span>
									</div>
								{/if}

								<div class="space-y-1">
									<div class="flex items-center gap-2 flex-wrap">
										<span class="font-bold text-sm text-zinc-100 {item.status === 'done' ? 'line-through text-zinc-500' : ''}">
											{item.title}
										</span>
										{#if item.event_type === 'ds'}
											<Badge variant="ds">Contrôle / DS</Badge>
										{:else if item.event_type === 'tp'}
											<Badge variant="tp">TP Noté</Badge>
										{:else}
											<Badge variant="secondary">Devoir Maison</Badge>
										{/if}
										{#if !item.is_personal}
											<Badge variant="warning" class="text-[10px]">Moodle UM</Badge>
										{/if}
									</div>

									<div class="text-xs font-medium text-cyan-400">
										{item.subject}
									</div>

									{#if item.description}
										<p class="text-xs text-zinc-400 mt-2 max-w-2xl bg-app-surface p-2.5 rounded-lg border border-app-border">
											{item.description}
										</p>
									{/if}
								</div>
							</div>

							<!-- Right side: Countdown & Delete -->
							<div class="flex flex-col items-end shrink-0 gap-2">
								<span class="text-xs font-medium px-3 py-0.5 rounded-full {item.days_left <= 2 ? 'bg-rose-600 text-white' : item.days_left <= 5 ? 'bg-amber-600 text-white' : 'bg-zinc-800 text-zinc-200'}">
									{#if item.status === 'done'}
										Terminé
									{:else if item.days_left <= 0}
										Aujourd'hui
									{:else if item.days_left === 1}
										Demain
									{:else}
										Dans {item.days_left} jours
									{/if}
								</span>

								<div class="text-xs text-zinc-500 flex items-center gap-1">
									<Calendar class="w-3 h-3" />
									<span>{formatDateFr(item.due_date)}</span>
								</div>

								{#if item.is_personal}
									<button
										onclick={() => deleteTask(item.id)}
										class="p-1 text-zinc-500 hover:text-red-400 hover:bg-white/[0.04] rounded transition-colors cursor-pointer mt-1"
										title="Supprimer"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								{/if}
							</div>
						</div>
					</Card>
				{/each}
			{/if}
		</div>
	{/if}
</div>
