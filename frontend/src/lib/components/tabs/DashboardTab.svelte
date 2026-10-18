<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { formatGrade, formatDateFr, toLocalIsoDate, getMondayOfDate, getCourseColorStyle } from "$lib/utils";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import {
		Plus,
		Check,
		Square,
		CheckSquare2,
		Clock,
		Calendar,
		RefreshCw,
		ArrowUpRight,
		MapPin,
		User as UserIcon,
		AlertCircle
	} from "lucide-svelte";

	let {
		onOpenAddTask,
		onNavigate,
		tasksRefreshTrigger = 0
	}: {
		onOpenAddTask?: () => void;
		onNavigate?: (tab: string) => void;
		tasksRefreshTrigger?: number;
	} = $props();

	let lastDashboardTrigger = $state(0);
	$effect(() => {
		if (tasksRefreshTrigger > lastDashboardTrigger) {
			lastDashboardTrigger = tasksRefreshTrigger;
			loadOverview(true);
		}
	});

	let overview = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let isRefreshing = $state(false);

	import { auth } from "$lib/stores/auth.svelte";

	async function loadOverview(silent = false, forceRefresh = false) {
		if (!silent) isLoading = true;
		error = "";
		try {
			overview = await api.getDashboardOverview(forceRefresh);
			if (overview?.user?.photo_base64 && auth.user) {
				auth.user.photo_base64 = overview.user.photo_base64;
				if (typeof window !== "undefined") {
					localStorage.setItem("cisco_user", JSON.stringify(auth.user));
				}
			}
		} catch (err: any) {
			error = err.message || "Erreur lors du chargement des données.";
		} finally {
			isLoading = false;
			isRefreshing = false;
		}
	}

	async function toggleTaskStatus(task: any) {
		const currentDone = task.status === "done" || task.done;
		const newStatus = currentDone ? "todo" : "done";
		task.done = !currentDone;
		task.status = newStatus;
		try {
			await api.toggleItemStatus(task.id, newStatus);
			await loadOverview(true);
		} catch (e) {
			console.error(e);
		}
	}

	onMount(() => {
		loadOverview();
	});

	// Calcul jauge circulaire moyenne generale
	let gpaValue = $derived(() => {
		const val = overview?.stats?.moyenne_generale;
		if (typeof val === "number" && !isNaN(val)) return val;
		return 0;
	});

	const radius = 28;
	const circumference = 2 * Math.PI * radius;
	let strokeDashoffset = $derived(() => {
		const score = gpaValue();
		const ratio = Math.min(Math.max(score / 20, 0), 1);
		return circumference * (1 - ratio);
	});

	let unjustifiedCount = $derived(() => {
		return overview?.absences?.injustifiees_demi_journees ?? overview?.absences?.injustifiees_nb ?? 0;
	});

	// Prochain cours reel
	let nextClassInfo = $derived(() => {
		if (overview?.current_course) {
			return {
				isLive: true,
				title: overview.current_course.title,
				subtitle: `${overview.current_course.location || "Salle"} • ${overview.current_course.teacher || "Enseignant"}`,
				statusText: "En ce moment",
				time: `${overview.current_course.start_time} - ${overview.current_course.end_time}`
			};
		}
		if (overview?.next_course) {
			return {
				isLive: false,
				title: overview.next_course.title,
				subtitle: `${overview.next_course.location || "Salle"} • ${overview.next_course.teacher || "Enseignant"}`,
				statusText: overview.next_course.day_name ? `${overview.next_course.day_name} à ${overview.next_course.start_time}` : `À ${overview.next_course.start_time}`,
				time: `${overview.next_course.start_time} - ${overview.next_course.end_time}`
			};
		}
		return null;
	});

	// Calcul des 5 jours de la semaine courante (Lundi a Vendredi)
	const now = new Date();
	const currentWeekday = (now.getDay() + 6) % 7;
	const mondayDate = getMondayOfDate(now, 0);

	const weekDays = [0, 1, 2, 3, 4].map((offset) => {
		const d = new Date(mondayDate);
		d.setDate(mondayDate.getDate() + offset);
		const dayNames = ["Lun", "Mar", "Mer", "Jeu", "Ven"];
		return {
			name: dayNames[offset],
			offset,
			isoDate: toLocalIsoDate(d),
			formattedDate: `${d.getDate()} / ${(d.getMonth() + 1).toString().padStart(2, "0")}`
		};
	});

	// Heures de la journee : de 8h00 a 18h30 (total 630 minutes)
	const dayStartMinutes = 8 * 60; // 480
	const dayEndMinutes = 18 * 60 + 30; // 1110
	const totalDayMinutes = dayEndMinutes - dayStartMinutes; // 630

	function parseTimeToMinutes(timeStr: string): number {
		if (!timeStr) return 0;
		const [h, m] = timeStr.split(":").map((v) => parseInt(v, 10));
		return h * 60 + (m || 0);
	}

	// Filtrage des cours reels de la semaine courante
	let weekEvents = $derived(() => {
		const raw = overview?.timetable_events || [];
		if (!raw || raw.length === 0) return [];

		const mondayIso = weekDays[0].isoDate;
		const fridayIso = weekDays[4].isoDate;

		return raw
			.filter((e: any) => e.date >= mondayIso && e.date <= fridayIso)
			.map((e: any) => {
				const startMins = parseTimeToMinutes(e.start_time);
				const endMins = parseTimeToMinutes(e.end_time);
				const duration = Math.max(endMins - startMins, 45);

				// Jour (0 a 4)
				const dayIdx = weekDays.findIndex((d) => d.isoDate === e.date);

				const topPercent = Math.min(Math.max(((startMins - dayStartMinutes) / totalDayMinutes) * 100, 0), 90);
				const heightPercent = Math.min(Math.max((duration / totalDayMinutes) * 100, 6), 50);

				const colorStyle = getCourseColorStyle(e.type);

				return {
					...e,
					dayIdx,
					topPercent,
					heightPercent,
					colorStyle
				};
			});
	});

	// Calcul indicateur horizontal heure actuelle
	let currentTimeIndicator = $derived(() => {
		const currentWeekday = (now.getDay() + 6) % 7;
		if (currentWeekday > 4) return null; // Pas d'indicateur le week-end
		const currentMins = now.getHours() * 60 + now.getMinutes();
		if (currentMins < dayStartMinutes || currentMins > dayEndMinutes) return null;

		const topPercent = ((currentMins - dayStartMinutes) / totalDayMinutes) * 100;
		const hoursStr = now.getHours().toString().padStart(2, "0");
		const minsStr = now.getMinutes().toString().padStart(2, "0");

		return {
			topPercent,
			dayIdx: currentWeekday,
			timeLabel: `${hoursStr}:${minsStr}`
		};
	});

	// Devoirs et echeances (4 premieres echeances)
	let upcomingTasks = $derived(() => {
		return (overview?.upcoming_tasks || []).slice(0, 4);
	});

	// Dernieres notes reelles
	let recentGrades = $derived(() => {
		return overview?.recent_grades || [];
	});
</script>

{#if isLoading && !overview}
	<div class="space-y-6">
		<!-- Ligne 1 : 3 KPI Skeletons -->
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
			<!-- KPI 1 Skeleton -->
			<Card class="flex items-center justify-between relative p-5">
				<div class="space-y-3 w-full">
					<div class="space-y-1.5">
						<Skeleton class="h-3 w-28" />
						<Skeleton class="h-2.5 w-36" />
					</div>
					<div class="flex items-baseline gap-2">
						<Skeleton class="h-9 w-24" />
						<Skeleton class="h-4 w-8" />
					</div>
					<Skeleton class="h-3 w-36" />
				</div>
				<Skeleton class="w-16 h-16 rounded-full shrink-0" />
			</Card>

			<!-- KPI 2 Skeleton -->
			<Card class="flex flex-col justify-between p-5 space-y-4">
				<div class="space-y-2">
					<Skeleton class="h-4 w-24 rounded-full" />
					<Skeleton class="h-5 w-44" />
					<Skeleton class="h-3 w-32" />
				</div>
				<div class="pt-3 border-t border-app-border flex items-center justify-between">
					<Skeleton class="h-3 w-28" />
					<Skeleton class="h-3 w-20" />
				</div>
			</Card>

			<!-- KPI 3 Skeleton -->
			<Card class="flex flex-col justify-between p-5 space-y-4">
				<div class="space-y-2">
					<Skeleton class="h-3 w-28" />
					<Skeleton class="h-2.5 w-36" />
					<Skeleton class="h-9 w-16" />
				</div>
				<div class="pt-3 border-t border-app-border flex items-center justify-between">
					<Skeleton class="h-3 w-24" />
					<Skeleton class="h-4 w-20 rounded-full" />
				</div>
			</Card>
		</div>

		<!-- Ligne 2 : Timetable Skeleton -->
		<Card class="space-y-4 p-5">
			<div class="flex items-center justify-between">
				<div class="space-y-1.5">
					<Skeleton class="h-4 w-48" />
					<Skeleton class="h-3 w-32" />
				</div>
				<Skeleton class="h-3 w-24" />
			</div>

			<!-- Semaine 5 jours skeleton -->
			<div class="grid grid-cols-5 gap-3 pt-2">
				{#each Array(5) as _}
					<div class="space-y-3">
						<Skeleton class="h-10 w-full rounded-lg" />
						<div class="h-56 rounded-lg border border-app-border bg-app-surface/50 p-2 space-y-2">
							<Skeleton class="h-16 w-full rounded-md" />
							<Skeleton class="h-20 w-full rounded-md" />
						</div>
					</div>
				{/each}
			</div>
		</Card>

		<!-- Ligne 3 : Devoirs & Dernieres notes Skeleton -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
			<Card class="space-y-4 p-5">
				<div class="flex items-center justify-between">
					<div class="space-y-1.5">
						<Skeleton class="h-4 w-36" />
						<Skeleton class="h-3 w-28" />
					</div>
					<Skeleton class="h-3 w-20" />
				</div>
				<div class="space-y-2.5">
					{#each Array(3) as _}
						<div class="flex items-center justify-between p-3 rounded-lg border border-app-border bg-app-surface/40">
							<div class="flex items-center gap-3">
								<Skeleton class="w-5 h-5 rounded-full shrink-0" />
								<div class="space-y-1.5">
									<Skeleton class="h-3.5 w-36" />
									<Skeleton class="h-2.5 w-24" />
								</div>
							</div>
							<Skeleton class="h-5 w-16 rounded-full" />
						</div>
					{/each}
				</div>
			</Card>

			<Card class="space-y-4 p-5">
				<div class="flex items-center justify-between">
					<div class="space-y-1.5">
						<Skeleton class="h-4 w-32" />
						<Skeleton class="h-3 w-40" />
					</div>
					<Skeleton class="h-3 w-24" />
				</div>
				<div class="space-y-2.5">
					{#each Array(3) as _}
						<div class="flex items-center justify-between p-3 rounded-lg border border-app-border bg-app-surface/40">
							<div class="space-y-1.5">
								<Skeleton class="h-3.5 w-40" />
								<Skeleton class="h-2.5 w-20" />
							</div>
							<Skeleton class="h-6 w-12 rounded-full" />
						</div>
					{/each}
				</div>
			</Card>
		</div>
	</div>
{:else if error}
	<div class="p-4 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
		{error}
	</div>
{:else}
	<div class="space-y-6">
		<!-- Ligne 1 : 3 KPI Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
		<!-- KPI 1 : Moyenne generale -->
		<Card class="flex items-center justify-between relative">
			<div class="space-y-2">
				<div class="space-y-0.5">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Moyenne générale</h3>
					<p class="text-xs text-zinc-500">Relevé ScoDoc</p>
				</div>
				<div class="flex items-baseline gap-1">
					<span class="text-3xl font-extrabold text-white tracking-tight">
						{gpaValue() > 0 ? gpaValue().toFixed(2) : "--"}
					</span>
					<span class="text-sm font-semibold text-zinc-500">/20</span>
				</div>
				<div class="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
					{#if overview?.stats?.rang}
						<span>Rang #{overview.stats.rang} sur {overview.stats.total_promo || 66} étudiants</span>
					{:else}
						<span>Semestre en cours</span>
					{/if}
				</div>
			</div>

			<!-- Jauge circulaire en cyan profond -->
			<div class="relative w-18 h-18 flex items-center justify-center shrink-0">
				<svg class="w-18 h-18 -rotate-90" viewBox="0 0 72 72">
					<circle
						cx="36"
						cy="36"
						r={radius}
						fill="transparent"
						stroke="var(--color-app-border)"
						stroke-width="5"
					/>
					<circle
						cx="36"
						cy="36"
						r={radius}
						fill="transparent"
						stroke="#0891B2"
						stroke-width="5"
						stroke-linecap="round"
						stroke-dasharray={circumference}
						stroke-dashoffset={strokeDashoffset()}
						class="transition-all duration-700 ease-out"
					/>
				</svg>
			</div>
		</Card>

		<!-- KPI 2 : Absences non justifiees -->
		<Card
			class="flex flex-col justify-between {onNavigate ? 'cursor-pointer hover:border-zinc-700 transition-colors' : ''}"
			onclick={() => onNavigate && onNavigate("absences")}
		>
			<div class="space-y-0.5">
				<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Absences non justifiées</h3>
				<p class="text-xs text-zinc-500">
					{overview?.absences?.total_heures ? `${overview.absences.total_heures} h manquées au total` : "Relevé à jour"}
				</p>
			</div>

			<div class="my-2 flex items-baseline gap-1.5">
				<span class="text-3xl font-extrabold text-white tracking-tight">
					{unjustifiedCount()}
				</span>
				<span class="text-xs text-zinc-400">demi-journée{unjustifiedCount() > 1 ? 's' : ''}</span>
			</div>

			<div>
				{#if unjustifiedCount() > 0}
					<span class="inline-flex items-center px-3 py-0.5 rounded-full text-xs font-medium bg-rose-600 text-white">
						Justification requise
					</span>
				{:else}
					<span class="inline-flex items-center px-3 py-0.5 rounded-full text-xs font-medium bg-emerald-600 text-white">
						Toutes justifiées
					</span>
				{/if}
			</div>
		</Card>

		<!-- KPI 3 : Prochain cours -->
		<Card class="flex flex-col justify-between">
			<div class="space-y-0.5">
				<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Prochain cours</h3>
				<p class="text-xs text-zinc-500">Emploi du temps</p>
			</div>

			{#if nextClassInfo()}
				<div class="my-1.5 space-y-1">
					<div class="text-sm font-bold text-white truncate" title={nextClassInfo()?.title}>
						{nextClassInfo()?.title}
					</div>
					<div class="text-xs text-zinc-400 truncate">
						{nextClassInfo()?.subtitle}
					</div>
				</div>

				<div class="flex items-center justify-between text-xs text-zinc-400 border-t border-app-border pt-2.5">
					<span class="font-medium text-cyan-400">{nextClassInfo()?.statusText}</span>
					<span class="text-zinc-500">{nextClassInfo()?.time}</span>
				</div>
			{:else}
				<div class="my-auto py-2">
					<p class="text-xs text-zinc-500">Aucun cours imminent programmé</p>
				</div>
			{/if}
		</Card>
	</div>

	<!-- Ligne 2 : Emploi du temps et Devoirs (sans empilement de boites) -->
	<div class="grid grid-cols-1 md:grid-cols-12 gap-5">
		<!-- Colonne Gauche : Emploi du temps (8 cols) -->
		<Card class="md:col-span-8 space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-sm font-bold text-white">Emploi du temps</h2>
					<p class="text-xs text-zinc-500">
						Du {weekDays[0].formattedDate} au {weekDays[4].formattedDate}
					</p>
				</div>
				{#if onNavigate}
					<button
						onclick={() => onNavigate("timetable")}
						class="text-xs text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer font-medium"
					>
						Voir tout <ArrowUpRight class="w-3 h-3" />
					</button>
				{/if}
			</div>

			{#if weekEvents().length === 0}
				<!-- Message clair sans faux template -->
				<div class="py-16 text-center border border-dashed border-app-border bg-app-surface/50 rounded-lg text-zinc-500 text-xs space-y-1">
					<p class="font-medium text-zinc-400">Aucun cours programmé pour cette semaine.</p>
					<p class="text-[11px]">Si l'emploi du temps devrait s'afficher, vérifiez votre lien iCal dans les Paramètres.</p>
				</div>
			{:else}
				<!-- Grille directe sur le fond de la carte -->
				<div>
					<!-- En-tetes des jours -->
					<div class="grid grid-cols-6 border-b border-app-border pb-2 text-center text-xs font-medium text-zinc-400">
						<div class="text-left pl-1 text-zinc-500">Heure</div>
						{#each weekDays as day, i}
							<div class="{currentWeekday === i ? 'text-cyan-400 font-bold' : ''}">
								<span>{day.name}</span>
								<span class="block text-[10px] text-zinc-500">{day.formattedDate}</span>
							</div>
						{/each}
					</div>

					<!-- Corps du calendrier : 5 colonnes de jours avec separateurs fins -->
					<div class="relative h-88 grid grid-cols-6 divide-x divide-app-border">
						<!-- Axe des heures a gauche -->
						<div class="flex flex-col justify-between py-1 text-[10px] text-zinc-500 pr-2">
							<span>08:00</span>
							<span>09:30</span>
							<span>11:00</span>
							<span>12:30</span>
							<span>14:00</span>
							<span>15:30</span>
							<span>17:00</span>
							<span>18:30</span>
						</div>

						<!-- 5 colonnes de jours -->
						{#each weekDays as day, dayIdx}
							<div class="relative h-full">
								<!-- Lignes de repere horizontales discretes -->
								<div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
									<div class="border-b border-zinc-700 w-full"></div>
									<div class="border-b border-zinc-700 w-full"></div>
									<div class="border-b border-zinc-700 w-full"></div>
									<div class="border-b border-zinc-700 w-full"></div>
									<div class="border-b border-zinc-700 w-full"></div>
									<div class="border-b border-zinc-700 w-full"></div>
									<div class="border-b border-zinc-700 w-full"></div>
								</div>

								<!-- Ligne horizontale de l'heure actuelle (uniquement sur le jour actuel) -->
								{#if currentTimeIndicator() && currentTimeIndicator()?.dayIdx === dayIdx}
									<div
										class="absolute left-0 right-0 z-30 pointer-events-none flex items-center"
										style="top: {currentTimeIndicator()?.topPercent}%;"
									>
										<div class="w-1.5 h-1.5 rounded-full bg-red-500 -ml-1"></div>
										<div class="h-0.5 w-full bg-red-500"></div>
										<span class="text-[9px] font-bold text-white bg-red-600 px-1 py-0.5 rounded ml-0.5 whitespace-nowrap shadow-xs">
											{currentTimeIndicator()?.timeLabel}
										</span>
									</div>
								{/if}

								<!-- Cours reels de la journee -->
								{#each weekEvents().filter((e: any) => e.dayIdx === dayIdx) as ev}
									<div
										style="top: {ev.topPercent}%; height: {ev.heightPercent}%;"
										class="absolute left-1 right-1 rounded-md p-2 text-xs font-sans border overflow-hidden transition-all hover:brightness-125 cursor-pointer z-10 {ev.colorStyle}"
										title="{ev.title} ({ev.start_time} - {ev.end_time}) - {ev.location}"
									>
										<div class="font-semibold truncate text-[11px] leading-tight">
											{ev.title}
										</div>
										<div class="text-[10px] opacity-80 truncate mt-0.5">
											{ev.location}
										</div>
										<div class="text-[9px] opacity-75 mt-0.5">
											{ev.start_time} - {ev.end_time}
										</div>
									</div>
								{/each}
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</Card>

		<!-- Colonne Droite : Devoirs à venir (4 cols) -->
		<Card class="md:col-span-4 flex flex-col justify-between space-y-4">
			<div>
				<div class="space-y-0.5 mb-3">
					<h2 class="text-sm font-bold text-white">Devoirs à venir</h2>
					<p class="text-xs text-zinc-500">Devoirs et échéances</p>
				</div>

				<div class="space-y-2.5">
					{#if upcomingTasks().length === 0}
						<div class="py-12 text-center text-zinc-500 text-xs">
							Aucun devoir à venir.
						</div>
					{:else}
						{#each upcomingTasks() as item}
							<div class="flex items-start gap-3 p-3 rounded-lg bg-app-surface border border-app-border hover:border-zinc-700 transition-colors">
								<!-- Bouton case a cocher -->
								<button
									onclick={() => toggleTaskStatus(item)}
									class="mt-0.5 text-zinc-500 hover:text-cyan-400 transition-colors cursor-pointer shrink-0"
									title="Marquer comme fait"
								>
									{#if item.status === "done" || item.done}
										<CheckSquare2 class="w-4 h-4 text-cyan-400" />
									{:else}
										<Square class="w-4 h-4 text-zinc-500 hover:text-zinc-300" />
									{/if}
								</button>

								<div class="space-y-1 flex-1 min-w-0">
									<div class="flex items-center gap-1.5 flex-wrap">
										<span class="text-xs font-semibold text-zinc-200 truncate {item.status === 'done' || item.done ? 'line-through text-zinc-500' : ''}">
											{item.title}
										</span>
										{#if item.days_left <= 2}
											<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-600 text-white">
												Urgent
											</span>
										{/if}
										{#if item.type === "ds" || item.source === "timetable"}
											<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-600 text-white">
												DS
											</span>
										{:else if item.source === "moodle"}
											<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-600 text-white">
												Moodle
											</span>
										{/if}
									</div>
									<div class="text-[11px] text-zinc-500">
										{item.days_left === 0 ? "Aujourd'hui à 23:59" : item.days_left === 1 ? "Demain" : `Dans ${item.days_left} jours (${formatDateFr(item.due_date)})`}
									</div>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<!-- Bouton d'ajout -->
			{#if onOpenAddTask}
				<button
					onclick={onOpenAddTask}
					class="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-dashed border-app-border hover:border-cyan-500/50 bg-app-surface hover:bg-white/[0.04] text-xs font-semibold text-zinc-300 hover:text-white transition-all cursor-pointer"
				>
					<Plus class="w-4 h-4 text-cyan-400" />
					<span>Ajouter un devoir</span>
				</button>
			{/if}
		</Card>
	</div>

	<!-- Ligne 3 : Dernieres notes de ScoDoc -->
	<Card class="space-y-4">
		<div class="flex items-center justify-between">
			<div>
				<h2 class="text-sm font-bold text-white">Dernières notes</h2>
				<p class="text-xs text-zinc-500">Évaluations synchronisées depuis ScoDoc</p>
			</div>
			{#if onNavigate}
				<button
					onclick={() => onNavigate("grades")}
					class="text-xs text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer font-medium"
				>
					Voir toutes les notes <ArrowUpRight class="w-3 h-3" />
				</button>
			{/if}
		</div>

		{#if recentGrades().length === 0}
			<div class="py-8 text-center text-zinc-500 text-xs">
				Aucune note récente enregistrée sur votre compte ScoDoc.
			</div>
		{:else}
			<div class="overflow-x-auto rounded-lg border border-app-border">
				<table class="w-full text-left text-xs">
					<thead class="bg-app-surface text-zinc-400 border-b border-app-border font-medium">
						<tr>
							<th class="py-3 px-4">Matière</th>
							<th class="py-3 px-4">Type</th>
							<th class="py-3 px-4">Date</th>
							<th class="py-3 px-4 text-right">Note</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-app-border bg-app-card">
						{#each recentGrades() as grade}
							<tr class="hover:bg-app-hover transition-colors">
								<td class="py-3 px-4 font-semibold text-zinc-200">
									<div class="flex items-center gap-2">
										{#if grade.code_matiere}
											<span class="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 font-semibold">
												{grade.code_matiere}
											</span>
										{/if}
										<span class="truncate">{grade.titre_matiere || grade.matiere_nom || grade.matiere || grade.nom || "Évaluation"}</span>
									</div>
								</td>
								<td class="py-3 px-4 text-zinc-400">
									<span class="px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 text-[11px] font-medium">
										{grade.description || grade.type || "Note"}
									</span>
								</td>
								<td class="py-3 px-4 text-zinc-400 text-[11px]">
									{grade.date ? formatDateFr(grade.date) : "Récent"}
								</td>
								<td class="py-3 px-4 text-right">
									<span class="inline-block px-2.5 py-0.5 rounded-full font-bold text-xs bg-cyan-600 text-white">
										{formatGrade(grade.note)}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</Card>
</div>
{/if}
