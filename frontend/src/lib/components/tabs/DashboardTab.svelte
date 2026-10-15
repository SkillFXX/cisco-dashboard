<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Badge from "../Badge.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { formatGrade, formatDateFr } from "$lib/utils";
	import {
		GraduationCap,
		AlertTriangle,
		Clock,
		Calendar,
		ArrowUpRight,
		CheckCircle2,
		Circle,
		BookOpen,
		MapPin,
		User as UserIcon,
		Layers,
		Sparkles,
		PlusCircle,
		RefreshCw
	} from "lucide-svelte";

	let {
		onOpenAddTask,
		onNavigate
	}: {
		onOpenAddTask?: () => void;
		onNavigate?: (tab: string) => void;
	} = $props();

	let overview = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let isRefreshing = $state(false);

	async function loadOverview(silent = false) {
		if (!silent) isLoading = true;
		error = "";
		try {
			overview = await api.getDashboardOverview();
		} catch (err: any) {
			error = err.message || "Erreur lors du chargement des données.";
		} finally {
			isLoading = false;
			isRefreshing = false;
		}
	}

	async function refreshData() {
		isRefreshing = true;
		await loadOverview(true);
	}

	async function toggleTaskStatus(task: any) {
		if (!task.is_personal) return;
		try {
			const newStatus = task.status === "done" ? "todo" : "done";
			await api.updateTask(task.task_id, { status: newStatus });
			await loadOverview(true);
		} catch (e) {
			console.error(e);
		}
	}

	onMount(() => {
		loadOverview();
	});
</script>

<div class="space-y-6">
	<!-- Top Welcome & Status Bar -->
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-zinc-900 via-zinc-900 to-zinc-950 p-6 rounded-2xl border border-zinc-800 shadow-sm">
		<div>
			<div class="flex items-center gap-2 mb-1">
				<Badge variant="cisco" class="font-mono text-xs">
					<Sparkles class="w-3 h-3 mr-1 inline" />
					Session Active
				</Badge>
				{#if overview?.services_status?.scodoc && overview?.services_status?.moodle && overview?.services_status?.ical}
					<Badge variant="success" class="text-xs">
						Services Connectés
					</Badge>
				{:else if overview?.services_status?.scodoc || overview?.services_status?.moodle || overview?.services_status?.ical}
					<Badge variant="success" class="text-xs">
						Partiellement Connecté
					</Badge>
				{:else}
					<Badge variant="outline" class="text-xs text-zinc-400">
						Services à configurer
					</Badge>
				{/if}
			</div>
			<h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white">
				Bonjour, {overview?.user?.full_name || "Étudiant"} 👋
			</h1>
			<p class="text-sm text-zinc-400 mt-1">
				Bienvenue sur votre espace centralisé Réseaux & Télécoms. Vos données ScoDoc, Moodle et ADE sont synchronisées.
			</p>
		</div>

		<div class="flex items-center gap-3">
			<Button variant="outline" size="sm" onclick={refreshData} disabled={isRefreshing}>
				<RefreshCw class="w-4 h-4 {isRefreshing ? 'animate-spin' : ''}" />
				<span>Actualiser</span>
			</Button>
			{#if onOpenAddTask}
				<Button variant="cisco" size="sm" onclick={onOpenAddTask}>
					<PlusCircle class="w-4 h-4" />
					<span>Nouveau DS</span>
				</Button>
			{/if}
		</div>
	</div>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center p-12 text-zinc-400">
			<RefreshCw class="w-8 h-8 animate-spin text-cyan-400 mb-3" />
			<p class="text-sm">Synchronisation de vos services ScoDoc, Moodle & ADE...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
			{error}
		</div>
	{:else if overview}
		<!-- 4 Hero Metric KPI Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- KPI 1 : Moyenne Générale -->
			<Card class="relative overflow-hidden group hover:border-cyan-500/50 transition-colors">
				<div class="flex items-center justify-between mb-3">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Moyenne Générale</span>
					<div class="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
						<GraduationCap class="w-4 h-4" />
					</div>
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-extrabold text-white tracking-tight">
						{formatGrade(overview.stats.moyenne_generale)}
					</span>
					<span class="text-sm text-zinc-500 font-medium">/ 20</span>
				</div>
				<div class="mt-3 flex items-center justify-between text-xs text-zinc-400 border-t border-zinc-800/80 pt-2.5">
					<span>Rang promo : <strong class="text-cyan-400">{overview.stats.rang || "--"}</strong> / {overview.stats.total_promo || "--"}</span>
					<span>Moy. promo : {formatGrade(overview.stats.moy_promo)}</span>
				</div>
			</Card>

			<!-- KPI 2 : Absences Injustifiées -->
			<Card class="relative overflow-hidden group hover:border-red-500/50 transition-colors">
				<div class="flex items-center justify-between mb-3">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Absences Injustifiées</span>
					<div class="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center">
						<AlertTriangle class="w-4 h-4" />
					</div>
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-extrabold {overview.absences.injustifiees_nb > 0 ? 'text-red-400' : 'text-emerald-400'} tracking-tight">
						{overview.absences.injustifiees_nb}
					</span>
					<span class="text-sm text-zinc-500">
						créneau{overview.absences.injustifiees_nb > 1 ? 'x' : ''} ({overview.absences.injustifiees_heures}h)
					</span>
				</div>
				<div class="mt-3 flex items-center justify-between text-xs text-zinc-400 border-t border-zinc-800/80 pt-2.5">
					<span>Total absences : {overview.absences.total_nb} ({overview.absences.total_heures}h)</span>
					{#if overview.absences.injustifiees_nb > 0}
						<span class="text-red-400 font-medium">À régulariser</span>
					{:else}
						<span class="text-emerald-400 font-medium">Assiduité OK</span>
					{/if}
				</div>
			</Card>

			<!-- KPI 3 : Prochain Cours -->
			<Card class="relative overflow-hidden group hover:border-blue-500/50 transition-colors">
				<div class="flex items-center justify-between mb-3">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">
						{overview.current_course ? "Cours En Direct" : "Prochain Cours"}
					</span>
					<div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
						<Clock class="w-4 h-4" />
					</div>
				</div>
				{#if overview.current_course}
					<div class="space-y-1">
						<div class="text-base font-bold text-white truncate" title={overview.current_course.title}>
							{overview.current_course.title}
						</div>
						<div class="flex items-center gap-2 text-xs text-cyan-400 font-medium">
							<span>En ce moment • {overview.current_course.start_time} - {overview.current_course.end_time}</span>
						</div>
					</div>
				{:else if overview.next_course}
					<div class="space-y-1">
						<div class="text-base font-bold text-white truncate" title={overview.next_course.title}>
							{overview.next_course.title}
						</div>
						<div class="flex items-center gap-2 text-xs text-zinc-400">
							<span>{overview.next_course.day_name} à {overview.next_course.start_time}</span>
						</div>
					</div>
				{:else}
					<p class="text-sm text-zinc-500">Aucun cours imminent</p>
				{/if}
				<div class="mt-3 flex items-center gap-1.5 text-xs text-zinc-400 border-t border-zinc-800/80 pt-2.5 truncate">
					<MapPin class="w-3.5 h-3.5 shrink-0 text-zinc-500" />
					<span class="truncate">{(overview.current_course || overview.next_course)?.location || "Pas de salle"}</span>
				</div>
			</Card>

			<!-- KPI 4 : Devoirs & DS à rendre -->
			<Card class="relative overflow-hidden group hover:border-amber-500/50 transition-colors">
				<div class="flex items-center justify-between mb-3">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Devoirs & DS</span>
					<div class="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
						<Calendar class="w-4 h-4" />
					</div>
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-extrabold text-white tracking-tight">
						{overview.upcoming_tasks?.length || 0}
					</span>
					<span class="text-sm text-zinc-500">échéance{overview.upcoming_tasks?.length > 1 ? 's' : ''}</span>
				</div>
				<div class="mt-3 flex items-center justify-between text-xs text-zinc-400 border-t border-zinc-800/80 pt-2.5">
					<span>Moodle & Contrôles</span>
					<button
						onclick={() => onNavigate && onNavigate("tasks")}
						class="text-amber-400 hover:text-amber-300 font-medium flex items-center gap-0.5 cursor-pointer"
					>
						Voir tout <ArrowUpRight class="w-3 h-3" />
					</button>
				</div>
			</Card>
		</div>

		<!-- Main 2-Column Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Left Column : Upcoming Assignments & Today's Schedule (2 cols) -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Prochains Devoirs & DS -->
				<Card>
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-2">
							<div class="w-7 h-7 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
								<BookOpen class="w-4 h-4" />
							</div>
							<h2 class="text-base font-semibold text-white">Prochains Devoirs & Évaluations</h2>
						</div>
						<div class="flex items-center gap-2">
							<Badge variant="outline" class="text-xs font-mono">
								{overview.upcoming_tasks?.length || 0} à venir
							</Badge>
							<button
								onclick={() => onNavigate && onNavigate("tasks")}
								class="text-xs text-cyan-400 hover:underline flex items-center gap-0.5 cursor-pointer ml-1"
							>
								Gérer <ArrowUpRight class="w-3 h-3" />
							</button>
						</div>
					</div>

					<div class="space-y-2.5">
						{#if !overview.upcoming_tasks || overview.upcoming_tasks.length === 0}
							<p class="text-sm text-zinc-500 text-center py-6">Aucun devoir ou contrôle programmé. Bravo !</p>
						{:else}
							{#each overview.upcoming_tasks as task}
								<div class="flex items-start justify-between p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-950/40 hover:bg-zinc-800/30 transition-colors group">
									<div class="flex items-start gap-3">
										{#if task.is_personal}
											<button
												onclick={() => toggleTaskStatus(task)}
												class="mt-0.5 text-zinc-500 hover:text-cyan-400 transition-colors cursor-pointer"
												title="Marquer comme fait"
											>
												<Circle class="w-4 h-4" />
											</button>
										{:else}
											<div class="mt-0.5 w-4 h-4 rounded-full border border-amber-500/40 bg-amber-500/10 flex items-center justify-center" title="Devoir Moodle">
												<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
											</div>
										{/if}

										<div>
											<div class="flex items-center gap-2 flex-wrap">
												<span class="font-medium text-sm text-zinc-100 group-hover:text-white transition-colors">
													{task.title}
												</span>
												{#if task.type === 'ds'}
													<Badge variant="ds">DS</Badge>
												{:else if task.type === 'tp'}
													<Badge variant="tp">TP</Badge>
												{:else}
													<Badge variant="secondary">DM</Badge>
												{/if}
												{#if !task.is_personal}
													<Badge variant="warning" class="text-[10px]">Moodle</Badge>
												{/if}
											</div>
											<p class="text-xs text-zinc-400 mt-1">
												{task.subject}
											</p>
										</div>
									</div>

									<div class="text-right shrink-0 ml-4">
										<span class="inline-block text-xs font-semibold px-2 py-0.5 rounded-md {task.days_left <= 2 ? 'bg-red-500/10 text-red-400 border border-red-500/20' : task.days_left <= 5 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-zinc-800 text-zinc-400'}">
											{task.days_left === 0 ? "Aujourd'hui" : task.days_left === 1 ? "Demain" : `Dans ${task.days_left} jours`}
										</span>
										<div class="text-[11px] text-zinc-500 mt-1">
											{formatDateFr(task.due_date)}
										</div>
									</div>
								</div>
							{/each}
						{/if}
					</div>
				</Card>

				<!-- Emploi du temps du jour -->
				<Card>
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-2">
							<div class="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
								<Clock class="w-4 h-4" />
							</div>
							<h2 class="text-base font-semibold text-white">Programme de la Journée</h2>
						</div>
						<button
							onclick={() => onNavigate && onNavigate("timetable")}
							class="text-xs text-cyan-400 hover:underline flex items-center gap-0.5 cursor-pointer"
						>
							Semaine complète <ArrowUpRight class="w-3 h-3" />
						</button>
					</div>

					<div class="space-y-3">
						{#if !overview.today_schedule || overview.today_schedule.length === 0}
							<div class="p-6 text-center text-sm text-zinc-500 rounded-xl bg-zinc-950/40 border border-zinc-800/80">
								Aucun cours programmé aujourd'hui sur votre emploi du temps ADE Campus.
							</div>
						{:else}
							<div class="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-zinc-800">
								{#each overview.today_schedule as evt}
									<div class="relative group">
										<!-- Dot indicator -->
										<div class="absolute -left-6 top-1.5 w-3 h-3 rounded-full border-2 {evt.is_current ? 'border-cyan-400 bg-cyan-400 animate-ping' : evt.is_passed ? 'border-zinc-700 bg-zinc-800' : 'border-blue-400 bg-zinc-900'}"></div>
										<div class="absolute -left-6 top-1.5 w-3 h-3 rounded-full border-2 {evt.is_current ? 'border-cyan-400 bg-cyan-400' : evt.is_passed ? 'border-zinc-700 bg-zinc-800' : 'border-blue-400 bg-zinc-900'}"></div>

										<div class="p-3 rounded-xl border {evt.is_current ? 'border-cyan-500/40 bg-cyan-950/20 shadow-md shadow-cyan-900/10' : 'border-zinc-800/80 bg-zinc-950/40'}">
											<div class="flex items-center justify-between gap-2">
												<div class="flex items-center gap-2">
													<span class="text-xs font-mono font-semibold text-zinc-300">
														{evt.start_time} - {evt.end_time}
													</span>
													{#if evt.type === 'TP'}
														<Badge variant="tp">TP</Badge>
													{:else if evt.type === 'TD'}
														<Badge variant="td">TD</Badge>
													{:else if evt.type === 'CM'}
														<Badge variant="cm">CM</Badge>
													{:else if evt.type === 'DS'}
														<Badge variant="ds">DS</Badge>
													{/if}
													{#if evt.is_current}
														<Badge variant="cisco">En cours</Badge>
													{/if}
												</div>
												<div class="flex items-center gap-1 text-xs text-zinc-400">
													<MapPin class="w-3 h-3 text-cyan-400" />
													<span>{evt.location}</span>
												</div>
											</div>
											<div class="font-medium text-sm text-zinc-100 mt-1">
												{evt.title}
											</div>
											{#if evt.teacher}
												<div class="text-xs text-zinc-500 mt-1">
													Enseignant : {evt.teacher}
												</div>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</Card>
			</div>

			<!-- Right Column : Recent ScoDoc Grades & Status (1 col) -->
			<div class="space-y-6">
				<!-- Dernières notes ScoDoc -->
				<Card>
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-2">
							<div class="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
								<GraduationCap class="w-4 h-4" />
							</div>
							<h2 class="text-base font-semibold text-white">Dernières Notes</h2>
						</div>
						<button
							onclick={() => onNavigate && onNavigate("grades")}
							class="text-xs text-cyan-400 hover:underline flex items-center gap-0.5 cursor-pointer"
						>
							Toutes les notes <ArrowUpRight class="w-3 h-3" />
						</button>
					</div>

					<div class="space-y-3">
						{#if !overview.recent_grades || overview.recent_grades.length === 0}
							<p class="text-sm text-zinc-500 text-center py-6">Aucune note saisie pour l'instant.</p>
						{:else}
							{#each overview.recent_grades as note}
								<div class="p-3 rounded-xl border border-zinc-800/80 bg-zinc-950/40 hover:bg-zinc-800/30 transition-colors">
									<div class="flex items-start justify-between gap-3">
										<div>
											<div class="flex items-center gap-1.5">
												<Badge variant="secondary" class="font-mono text-[10px]">
													{note.code_matiere}
												</Badge>
												<span class="text-xs text-zinc-400">Coef {note.coefficient}</span>
											</div>
											<div class="text-xs font-medium text-zinc-200 mt-1 line-clamp-1" title={note.description}>
												{note.description}
											</div>
											<div class="text-[10px] text-zinc-500 mt-0.5">
												Moyenne promo : {formatGrade(note.moy_promo)} • Max : {formatGrade(note.max_promo)}
											</div>
										</div>

										<div class="text-right shrink-0">
											<span class="text-lg font-extrabold {note.note !== null && note.note >= 10 ? 'text-emerald-400' : 'text-red-400'}">
												{formatGrade(note.note)}
											</span>
											<span class="text-xs text-zinc-500">/20</span>
											<div class="text-[10px] text-zinc-500 mt-0.5">
												{formatDateFr(note.date)}
											</div>
										</div>
									</div>
								</div>
							{/each}
						{/if}
					</div>
				</Card>

				<!-- État des services connectés -->
				<Card class="bg-gradient-to-b from-zinc-900 to-zinc-950">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-1.5">
						<Layers class="w-3.5 h-3.5 text-cyan-400" />
						Flux et Connecteurs
					</h3>

					<div class="space-y-2 text-xs">
						<div class="flex items-center justify-between p-2 rounded-lg bg-zinc-900/80 border border-zinc-800">
							<div class="flex items-center gap-2">
								<span class="w-2 h-2 rounded-full {overview.services_status?.scodoc ? 'bg-emerald-400' : 'bg-zinc-600'}"></span>
								<span class="text-zinc-300 font-medium">ScoDoc (Notes & Absences)</span>
							</div>
							<span class="text-zinc-500">{overview.services_status?.scodoc ? 'Connecté' : 'Non configuré'}</span>
						</div>

						<div class="flex items-center justify-between p-2 rounded-lg bg-zinc-900/80 border border-zinc-800">
							<div class="flex items-center gap-2">
								<span class="w-2 h-2 rounded-full {overview.services_status?.moodle ? 'bg-emerald-400' : 'bg-zinc-600'}"></span>
								<span class="text-zinc-300 font-medium">Moodle (Devoirs & DM)</span>
							</div>
							<span class="text-zinc-500">{overview.services_status?.moodle ? 'Connecté' : 'Non configuré'}</span>
						</div>

						<div class="flex items-center justify-between p-2 rounded-lg bg-zinc-900/80 border border-zinc-800">
							<div class="flex items-center gap-2">
								<span class="w-2 h-2 rounded-full {overview.services_status?.ical ? 'bg-emerald-400' : 'bg-zinc-600'}"></span>
								<span class="text-zinc-300 font-medium">ADE Campus (Emploi du temps)</span>
							</div>
							<span class="text-zinc-500">{overview.services_status?.ical ? 'Connecté' : 'Non configuré'}</span>
						</div>
					</div>

					<button
						onclick={() => onNavigate && onNavigate("settings")}
						class="w-full mt-3 py-1.5 text-xs text-center text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer block"
					>
						Gérer mes identifiants de connexion &rarr;
					</button>
				</Card>
			</div>
		</div>
	{/if}
</div>

