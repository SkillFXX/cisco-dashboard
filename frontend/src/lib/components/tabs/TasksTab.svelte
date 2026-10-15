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
		BookOpen,
		Filter,
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
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
				<ListTodo class="w-6 h-6 text-cyan-400" />
				Devoirs, DM Moodle & Dates de DS
			</h1>
			<p class="text-sm text-zinc-400 mt-1">
				Gérez l'ensemble de vos échéances : devoirs Moodle synchronisés et contrôles / DS ajoutés manuellement.
			</p>
		</div>

		<div class="flex items-center gap-3">
			<Button variant="outline" size="sm" onclick={loadAllData} disabled={isLoading}>
				<RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" />
				<span>Actualiser</span>
			</Button>
			{#if onOpenAddTask}
				<Button variant="cisco" size="sm" onclick={onOpenAddTask}>
					<PlusCircle class="w-4 h-4" />
					<span>Ajouter un DS / Devoir</span>
				</Button>
			{/if}
		</div>
	</div>

	<!-- Filters -->
	<div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none border-b border-zinc-800">
		{#each [
			{ id: 'ALL', label: 'Toutes les échéances' },
			{ id: 'TODO', label: 'À faire' },
			{ id: 'DS', label: 'Contrôles (DS)' },
			{ id: 'MOODLE', label: 'Moodle' },
			{ id: 'DONE', label: 'Terminés' }
		] as f}
			<button
				onclick={() => (filterType = f.id)}
				class="px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {filterType === f.id ? 'bg-cyan-500 text-zinc-950 shadow-md shadow-cyan-500/20' : 'bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800'}"
			>
				{f.label}
			</button>
		{/each}
	</div>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center p-12 text-zinc-400">
			<RefreshCw class="w-8 h-8 animate-spin text-cyan-400 mb-3" />
			<p class="text-sm">Chargement des devoirs et contrôles programmés...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
			{error}
		</div>
	{:else}
		<div class="space-y-3">
			{#if displayedItems().length === 0}
				<Card class="text-center py-12 text-zinc-500 text-sm">
					Aucun devoir ou contrôle correspondant à ce filtre.
				</Card>
			{:else}
				{#each displayedItems() as item}
					<div class="p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/60 hover:bg-zinc-800/40 transition-all {item.status === 'done' ? 'opacity-60' : ''}">
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
									<div class="mt-1 w-5 h-5 rounded-full border border-amber-500/40 bg-amber-500/10 flex items-center justify-center shrink-0" title="Synchronisé depuis Moodle">
										<span class="w-2 h-2 rounded-full bg-amber-400"></span>
									</div>
								{/if}

								<div class="space-y-1">
									<div class="flex items-center gap-2 flex-wrap">
										<span class="font-bold text-base text-zinc-100 {item.status === 'done' ? 'line-through text-zinc-400' : ''}">
											{item.title}
										</span>
										{#if item.event_type === 'ds'}
											<Badge variant="ds">DS / Examen</Badge>
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
										<p class="text-xs text-zinc-400 mt-2 max-w-2xl bg-zinc-950/40 p-2.5 rounded-lg border border-zinc-800/60">
											{item.description}
										</p>
									{/if}
								</div>
							</div>

							<!-- Right side: Countdown & Delete -->
							<div class="flex flex-col items-end shrink-0 gap-2">
								<span class="text-xs font-semibold px-2.5 py-1 rounded-md {item.days_left <= 2 ? 'bg-red-500/10 text-red-400 border border-red-500/30' : item.days_left <= 5 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-zinc-800 text-zinc-300'}">
									{#if item.status === 'done'}
										Terminé ✓
									{:else if item.days_left <= 0}
										Aujourd'hui !
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
										class="p-1 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded transition-colors cursor-pointer mt-1"
										title="Supprimer"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	{/if}
</div>

