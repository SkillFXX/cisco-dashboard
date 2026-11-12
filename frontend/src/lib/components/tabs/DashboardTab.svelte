<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { formatGrade, formatDateFr, toLocalIsoDate, getMondayOfDate, getCourseColorStyle } from "$lib/utils";
	import Card from "../Card.svelte";
	import DueLabel from "../DueLabel.svelte";
	import SeeAllLink from "../SeeAllLink.svelte";
	import Skeleton from "../Skeleton.svelte";
	import CourseDetailModal from "../CourseDetailModal.svelte";
	import AverageCard from "../AverageCard.svelte";
	import GradesTable from "../GradesTable.svelte";
	import {
		Plus,
		Check,
		Circle,
		CheckCircle2,
		Clock,
		Calendar,
		RefreshCw,
		MapPin,
		User as UserIcon,
		AlertCircle
	} from "lucide-svelte";

	let {
		onOpenAddTask,
		onNavigate,
		onAddTaskForCourse,
		tasksRefreshTrigger = 0
	}: {
		onAddTaskForCourse?: (course: any) => void;
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
	let gradeHistory = $state<number[]>([]);
	let isLoading = $state(true);
	let error = $state("");
	let isRefreshing = $state(false);

	import { auth } from "$lib/stores/auth.svelte";

	async function loadOverview(silent = false, forceRefresh = false) {
		if (!silent) isLoading = true;
		error = "";
		try {
			overview = await api.getDashboardOverview(forceRefresh);
			api.getGradeHistory()
				.then((h) => (gradeHistory = h.filter((p) => p.moyenne != null).map((p) => p.moyenne as number)))
				.catch(() => {});
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

	let unjustifiedCount = $derived(() => {
		return overview?.absences?.injustifiees_demi_journees ?? overview?.absences?.injustifiees_nb ?? 0;
	});

	// Detail d'un cours (modale partagee avec l'onglet Emploi du temps)
	let selectedCourse = $state<any>(null);
	let isCourseModalOpen = $state(false);
	function openCourse(course: any) {
		selectedCourse = course;
		isCourseModalOpen = true;
	}

	// Prochain cours reel
	let nextClassInfo = $derived(() => {
		if (overview?.current_course) {
			return {
				isLive: true,
				course: overview.current_course,
				title: overview.current_course.title,
				subtitle: `${overview.current_course.location || "Salle"} • ${overview.current_course.teacher || "Enseignant"}`,
				statusText: "En ce moment",
				time: `${overview.current_course.start_time} - ${overview.current_course.end_time}`
			};
		}
		if (overview?.next_course) {
			return {
				isLive: false,
				course: overview.next_course,
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
						<div class="h-56 space-y-2">
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
						<div class="flex items-center justify-between py-2">
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
						<div class="flex items-center justify-between py-2">
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
		<!-- KPI 1 : Moyenne générale (même carte que dans l'onglet Notes) -->
		<AverageCard stats={overview?.stats} series={gradeHistory} onclick={onNavigate ? () => onNavigate("grades") : undefined} />

		<!-- KPI 2 : Absences non justifiées -->
		<Card
			class="p-4 space-y-2 {onNavigate ? 'cursor-pointer hover:border-subtle transition-colors' : ''}"
			onclick={() => onNavigate && onNavigate("absences")}
		>
			<span class="text-[11px] font-semibold uppercase tracking-wider text-muted">Absences non justifiées</span>
			<div class="flex items-baseline gap-1.5">
				<span class="text-2xl sm:text-3xl font-black text-fg">{unjustifiedCount()}</span>
				<span class="text-xs text-subtle font-semibold">demi-journée{unjustifiedCount() > 1 ? "s" : ""}</span>
			</div>
			<div class="pt-1.5 border-t border-app-border text-[11px] text-muted">
				{#if unjustifiedCount() > 0}
					<span class="rounded-md px-2 py-0.5 font-semibold bg-rose-600/15 text-rose-400">À justifier</span>
				{:else}
					Tout est justifié
				{/if}
			</div>
		</Card>

		<!-- KPI 3 : Prochain cours -->
		<Card class="p-4 space-y-2">
			<span class="text-[11px] font-semibold uppercase tracking-wider text-muted">Prochain cours</span>
			{#if nextClassInfo()}
				<button type="button" onclick={() => openCourse(nextClassInfo()?.course)} class="block text-left w-full min-w-0 cursor-pointer hover:opacity-80 transition-opacity">
					<div class="text-base font-bold text-fg truncate" title={nextClassInfo()?.title}>{nextClassInfo()?.title}</div>
					<div class="text-xs text-muted truncate">{nextClassInfo()?.subtitle}</div>
				</button>
				<div class="pt-1.5 border-t border-app-border flex items-center justify-between text-[11px] text-muted">
					<span class="font-medium text-fg">{nextClassInfo()?.statusText}</span>
					<span>{nextClassInfo()?.time}</span>
				</div>
			{:else}
				<p class="text-xs text-subtle pt-1">Aucun cours à venir</p>
			{/if}
		</Card>
	</div>

	<!-- Ligne 2 : Emploi du temps et Devoirs (sans empilement de boites) -->
	<div class="grid grid-cols-1 md:grid-cols-12 gap-5">
		<!-- Colonne Gauche : Emploi du temps (8 cols) -->
		<Card class="md:col-span-8 space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-sm font-bold text-fg">Cette semaine</h2>
				</div>
				{#if onNavigate}
					<SeeAllLink onclick={() => onNavigate("timetable")} />
				{/if}
			</div>

			{#if weekEvents().length === 0}
				<!-- Message clair sans faux template -->
				<div class="py-16 text-center text-subtle text-xs space-y-1">
					<p class="font-medium text-muted">Aucun cours programmé pour cette semaine.</p>
					<p class="text-[11px]">Si l'emploi du temps devrait s'afficher, vérifiez votre lien iCal dans les Paramètres.</p>
				</div>
			{:else}
				<!-- Grille directe sur le fond de la carte -->
				<div>
					<!-- En-tetes des jours -->
					<div class="grid grid-cols-6 border-b border-app-border pb-2 text-center text-xs font-medium text-muted">
						<div class="text-left pl-1 text-subtle">Heure</div>
						{#each weekDays as day, i}
							<div>
								<span class="{currentWeekday === i ? 'rounded-md bg-cyan-600/15 text-cyan-400 px-2 py-0.5 font-semibold' : ''}">{day.name}</span>
								<span class="block text-[10px] text-subtle">{day.formattedDate}</span>
							</div>
						{/each}
					</div>

					<!-- Corps du calendrier : 5 colonnes de jours avec separateurs fins -->
					<div class="relative h-88 grid grid-cols-6 divide-x divide-app-border">
						<!-- Axe des heures a gauche -->
						<div class="flex flex-col justify-between py-1 text-[10px] text-subtle pr-2">
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
									<div class="border-b border-app-border w-full"></div>
									<div class="border-b border-app-border w-full"></div>
									<div class="border-b border-app-border w-full"></div>
									<div class="border-b border-app-border w-full"></div>
									<div class="border-b border-app-border w-full"></div>
									<div class="border-b border-app-border w-full"></div>
									<div class="border-b border-app-border w-full"></div>
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
									<button
										type="button"
										onclick={() => openCourse(ev)}
										style="top: {ev.topPercent}%; height: {ev.heightPercent}%;"
										class="absolute left-1 right-1 rounded-md p-2 text-xs font-sans overflow-hidden transition-all hover:brightness-95 cursor-pointer z-10 text-left {ev.colorStyle}"
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
									</button>
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
				<div class="flex items-center justify-between mb-3">
					<h2 class="text-sm font-bold text-fg">Devoirs à venir</h2>
					{#if onNavigate}
						<SeeAllLink onclick={() => onNavigate("tasks")} />
					{/if}
				</div>

				{#if upcomingTasks().length === 0}
					<div class="py-12 text-center text-subtle text-xs">
						Aucun devoir à venir.
					</div>
				{:else}
					<div class="divide-y divide-app-border">
						{#each upcomingTasks() as item}
							<div class="flex items-center justify-between py-3 gap-3 text-left">
								<!-- Checkbox + Titre & Description -->
								<div class="flex items-center gap-3.5 min-w-0 flex-1">
									<button
										type="button"
										onclick={(e) => {
											e.stopPropagation();
											toggleTaskStatus(item);
										}}
										class="text-subtle hover:text-cyan-400 transition-colors cursor-pointer shrink-0"
										title="Marquer comme fait"
									>
										{#if item.status === "done" || item.done}
											<CheckCircle2 class="w-5 h-5 text-emerald-400" />
										{:else}
											<Circle class="w-5 h-5" />
										{/if}
									</button>

									<div class="min-w-0 flex-1">
										<!-- Titre du devoir mis en évidence -->
										<div class="flex items-center gap-2">
											<span class="font-bold text-xs text-fg truncate {item.status === 'done' || item.done ? 'line-through text-subtle' : ''}">
												{item.title}
											</span>
										</div>
										<!-- Salle ou consignes sous le titre -->
										<p class="text-xs text-muted truncate mt-0.5">
											{[item.type === "ds" || item.category === "DS" || item.source === "timetable" ? "DS" : item.type === "dm" || item.category === "DM" || item.source === "moodle" ? "DM" : item.type === "tp" || item.category === "TP" ? "TP" : "", item.description].filter(Boolean).join(" · ")}
										</p>
									</div>
								</div>

								<!-- Date et délai (à droite) -->
								<div class="flex flex-col items-end shrink-0 text-right">
									<DueLabel daysLeft={item.days_left} />
									<span class="text-[10px] text-subtle mt-0.5">
										{formatDateFr(item.due_date)}
									</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Bouton d'ajout -->
			{#if onOpenAddTask}
				<button
					onclick={onOpenAddTask}
					class="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-dashed border-app-border hover:border-cyan-500/50 bg-app-surface hover:bg-fg/[0.04] text-xs font-semibold text-muted hover:text-fg transition-all cursor-pointer"
				>
					<Plus class="w-4 h-4 text-cyan-400" />
					<span>Ajouter un devoir</span>
				</button>
			{/if}
		</Card>
	</div>

	<!-- Ligne 3 : Dernières notes -->
	<Card class="space-y-2">
		<div class="flex items-center justify-between">
			<h2 class="text-sm font-bold text-fg">Dernières notes</h2>
			{#if onNavigate}
				<SeeAllLink onclick={() => onNavigate("grades")} />
			{/if}
		</div>
		<GradesTable rows={recentGrades()} onSelect={onNavigate ? () => onNavigate("grades") : undefined} emptyText="Aucune note récente." />
	</Card>
</div>
{/if}

<CourseDetailModal course={selectedCourse} bind:open={isCourseModalOpen} onAddTask={onAddTaskForCourse} />
