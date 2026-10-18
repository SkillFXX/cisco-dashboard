<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import { api } from "$lib/api";
	import { formatDateFr } from "$lib/utils";
	import {
		Clock,
		RefreshCw,
		X,
		Calendar,
		User as UserIcon,
		CheckCircle2,
		AlertCircle
	} from "lucide-svelte";

	let absencesData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let filterStatus = $state<string>("ALL"); // ALL, JUSTIFIED, UNJUSTIFIED, RETARD

	// Volet latéral de détail
	let selectedAbsence = $state<any>(null);

	function formatDuration(hours: number | null | undefined): string {
		if (hours === null || hours === undefined) return "--";
		const h = Math.floor(hours);
		const m = Math.round((hours - h) * 60);
		if (m === 0) return `${h}h`;
		return `${h}h${m.toString().padStart(2, "0")}`;
	}

	function formatFullDate(dateStr: string): string {
		if (!dateStr) return "--";
		try {
			const d = new Date(dateStr);
			return d.toLocaleDateString("fr-FR", {
				weekday: "long",
				day: "numeric",
				month: "long",
				year: "numeric"
			});
		} catch {
			return dateStr;
		}
	}

	async function loadAbsences(forceRefresh = false) {
		isLoading = true;
		error = "";
		try {
			absencesData = await api.getAbsences(forceRefresh);
		} catch (err: any) {
			error = err.message || "Erreur lors du chargement du bilan d'assiduité.";
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadAbsences();

		const handleKeyDown = (e: KeyboardEvent) => {
			if (e.key === "Escape") {
				selectedAbsence = null;
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	});

	let creneauxList = $derived(() => {
		const list = absencesData?.creneaux || [];
		if (filterStatus === "JUSTIFIED") {
			return list.filter((c: any) => c.justifie && c.type !== "retard");
		}
		if (filterStatus === "UNJUSTIFIED") {
			return list.filter((c: any) => !c.justifie && c.type !== "retard");
		}
		if (filterStatus === "RETARD") {
			return list.filter((c: any) => c.type === "retard" || c.statut === "Retard");
		}
		return list;
	});
</script>

<div class="space-y-6 relative">
	<!-- En-tête -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<Clock class="w-5 h-5 text-cyan-400" />
				<span>Bilan d'Assiduité & Absences</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Données extraites en temps réel de votre compte ScoDoc. Suivi officiel des demi-journées manquées et des retards.
			</p>
		</div>

		<button
			onclick={() => loadAbsences(true)}
			disabled={isLoading}
			class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-white/[0.04] border border-app-border text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
		>
			<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
			<span>Actualiser ScoDoc</span>
		</button>
	</div>

	{#if isLoading && !absencesData}
		<div class="space-y-6">
			<!-- 3 KPIs Skeletons -->
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
				{#each Array(3) as _}
					<Card class="flex flex-col justify-between py-4 px-5 space-y-4">
						<div class="space-y-2">
							<Skeleton class="h-3 w-32" />
							<div class="flex items-baseline gap-2">
								<Skeleton class="h-8 w-16" />
								<Skeleton class="h-3 w-24" />
							</div>
						</div>
						<div class="pt-3 border-t border-app-border flex items-center justify-between">
							<Skeleton class="h-3 w-28" />
							<Skeleton class="h-4 w-16 rounded-full" />
						</div>
					</Card>
				{/each}
			</div>

			<!-- Filtres Skeleton -->
			<div class="flex items-center gap-2 pb-1 border-b border-app-border">
				<Skeleton class="h-8 w-24 rounded-lg" />
				<Skeleton class="h-8 w-28 rounded-lg" />
				<Skeleton class="h-8 w-32 rounded-lg" />
				<Skeleton class="h-8 w-20 rounded-lg" />
			</div>

			<!-- Liste Skeleton -->
			<Card class="space-y-4 p-5">
				<div class="flex items-center justify-between">
					<div class="space-y-1.5">
						<Skeleton class="h-4 w-36" />
						<Skeleton class="h-3 w-48" />
					</div>
					<Skeleton class="h-3 w-24" />
				</div>

				<div class="border border-app-border rounded-xl overflow-hidden divide-y divide-white/5">
					{#each Array(4) as _}
						<div class="p-3.5 flex items-center justify-between bg-app-surface/30">
							<div class="flex items-center gap-3">
								<Skeleton class="w-8 h-8 rounded-lg shrink-0" />
								<div class="space-y-1.5">
									<Skeleton class="h-3.5 w-40" />
									<Skeleton class="h-2.5 w-28" />
								</div>
							</div>
							<div class="flex items-center gap-4">
								<Skeleton class="h-5 w-20 rounded-full" />
								<Skeleton class="h-3 w-20" />
							</div>
						</div>
					{/each}
				</div>
			</Card>
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
			{error}
		</div>
	{:else if absencesData}
		<!-- 3 KPIs : Absences justifiées (demi-journées), non justifiées (demi-journées), retards (nombre) -->
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
			<!-- KPI 1 : Absences justifiées (en demi-journées) -->
			<Card class="flex flex-col justify-between py-4 px-5">
				<div class="space-y-1">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Absences justifiées</h3>
					<div class="flex items-baseline gap-1.5">
						<span class="text-3xl font-extrabold text-white tracking-tight">
							{absencesData.justifiees_demi_journees ?? 0}
						</span>
						<span class="text-xs text-zinc-400">
							demi-journée{(absencesData.justifiees_demi_journees ?? 0) > 1 ? 's' : ''}
						</span>
					</div>
				</div>

				<div class="flex items-center justify-between pt-3 border-t border-app-border mt-3 text-xs">
					<span class="text-zinc-500">
						Volume : <span class="text-white font-medium">{absencesData.justifiees_heures ?? 0}h</span> ({absencesData.justifiees_nb ?? 0} créneau{(absencesData.justifiees_nb ?? 0) > 1 ? 'x' : ''})
					</span>
					<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
						Validées
					</span>
				</div>
			</Card>

			<!-- KPI 2 : Absences non justifiées (en demi-journées) -->
			<Card class="flex flex-col justify-between py-4 px-5">
				<div class="space-y-1">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Absences non justifiées</h3>
					<div class="flex items-baseline gap-1.5">
						<span class="text-3xl font-extrabold text-white tracking-tight">
							{absencesData.injustifiees_demi_journees ?? 0}
						</span>
						<span class="text-xs text-zinc-400">
							demi-journée{(absencesData.injustifiees_demi_journees ?? 0) > 1 ? 's' : ''}
						</span>
					</div>
				</div>

				<div class="flex items-center justify-between pt-3 border-t border-app-border mt-3 text-xs">
					<span class="text-zinc-500">
						Volume : <span class="text-white font-medium">{absencesData.injustifiees_heures ?? 0}h</span>
					</span>
					{#if (absencesData.injustifiees_demi_journees ?? 0) > 0}
						<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-rose-600 text-white">
							Justification requise
						</span>
					{:else}
						<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
							À jour
						</span>
					{/if}
				</div>
			</Card>

			<!-- KPI 3 : Retards (en nombre) -->
			<Card class="flex flex-col justify-between py-4 px-5">
				<div class="space-y-1">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Retards</h3>
					<div class="flex items-baseline gap-1.5">
						<span class="text-3xl font-extrabold text-white tracking-tight">
							{absencesData.retards_nb ?? 0}
						</span>
						<span class="text-xs text-zinc-400">retard{(absencesData.retards_nb ?? 0) > 1 ? 's' : ''}</span>
					</div>
				</div>

				<div class="flex items-center justify-between pt-3 border-t border-app-border mt-3 text-xs">
					<span class="text-zinc-500">
						Volume total manqué : <span class="text-white font-medium">{absencesData.total_heures ?? 0}h</span>
					</span>
					{#if (absencesData.retards_nb ?? 0) > 0}
						<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-amber-600 text-white">
							{absencesData.retards_nb} retard{(absencesData.retards_nb > 1 ? 's' : '')}
						</span>
					{:else}
						<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-zinc-100">
							À l'heure
						</span>
					{/if}
				</div>
			</Card>
		</div>

		<!-- Filtres de statut -->
		<div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-app-border">
			{#each [
				{ id: 'ALL', label: 'Toutes les absences', count: (absencesData.creneaux || []).length },
				{ id: 'JUSTIFIED', label: 'Justifiées', count: absencesData.justifiees_nb ?? 0 },
				{ id: 'UNJUSTIFIED', label: 'Non justifiées', count: absencesData.injustifiees_nb ?? 0 }
			] as f}
				<button
					onclick={() => (filterStatus = f.id)}
					class="px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer flex items-center gap-2 {filterStatus === f.id
						? 'bg-white/[0.08] text-white shadow-xs'
						: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
				>
					<span>{f.label}</span>
					<span class="px-1.5 py-0.2 rounded-full text-[10px] bg-white/[0.08] text-white">
						{f.count}
					</span>
				</button>
			{/each}
			{#if (absencesData.retards_nb ?? 0) > 0}
				<button
					onclick={() => (filterStatus = 'RETARD')}
					class="px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer flex items-center gap-2 {filterStatus === 'RETARD'
						? 'bg-white/[0.08] text-white shadow-xs'
						: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
				>
					<span>Retards</span>
					<span class="px-1.5 py-0.2 rounded-full text-[10px] bg-white/[0.08] text-white">
						{absencesData.retards_nb}
					</span>
				</button>
			{/if}
		</div>

		<!-- Tableau unifié des créneaux d'absence -->
		<div class="space-y-2">
			{#if creneauxList().length === 0}
				<div class="py-12 text-center border border-dashed border-app-border rounded-xl bg-app-card/40 text-zinc-500 text-xs">
					{#if filterStatus === 'UNJUSTIFIED'}
						Aucune absence non justifiée enregistrée. Votre assiduité est exemplaire.
					{:else if filterStatus === 'JUSTIFIED'}
						Aucune absence justifiée pour le moment.
					{:else if filterStatus === 'RETARD'}
						Aucun retard enregistré.
					{:else}
						Félicitations ! Aucune absence enregistrée sur ScoDoc ce semestre.
					{/if}
				</div>
			{:else}
				<div class="border border-app-border rounded-xl bg-app-card overflow-hidden">
					<!-- En-tête des colonnes -->
					<div class="grid grid-cols-12 px-4 py-3 border-b border-app-border text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
						<div class="col-span-6 sm:col-span-5">Matière & Horaires</div>
						<div class="hidden sm:block col-span-3">Enseignant</div>
						<div class="col-span-3 sm:col-span-2 text-right sm:text-center">Durée</div>
						<div class="col-span-3 sm:col-span-2 text-right">Statut</div>
					</div>

					<!-- Liste avec séparateurs fins et survol doux -->
					<div class="divide-y divide-white/5">
						{#each creneauxList() as c}
							<div
								role="button"
								tabindex="0"
								onclick={() => (selectedAbsence = c)}
								onkeydown={(e) => { if (e.key === 'Enter') selectedAbsence = c; }}
								class="grid grid-cols-12 items-center px-4 py-3 hover:bg-white/[0.02] transition-colors cursor-pointer gap-2 text-left"
							>
								<!-- Colonne 1 : Matière & Date/Heure -->
								<div class="col-span-6 sm:col-span-5 min-w-0 pr-2">
									<p class="font-bold text-xs text-white truncate">
										{c.matiere || "Module non précisé"}
									</p>
									<p class="text-[11px] text-zinc-400 mt-0.5 truncate">
										{formatDateFr(c.date)} • {c.heure_debut} - {c.heure_fin}
									</p>
								</div>

								<!-- Colonne 2 : Enseignant -->
								<div class="hidden sm:block col-span-3 text-xs text-zinc-400 truncate">
									{c.enseignant || "Non renseigné"}
								</div>

								<!-- Colonne 3 : Durée -->
								<div class="col-span-3 sm:col-span-2 text-right sm:text-center">
									<span class="text-xs font-semibold text-white">
										{formatDuration(c.duree_heures)}
									</span>
								</div>

								<!-- Colonne 4 : Statut avec badge rond plein -->
								<div class="col-span-3 sm:col-span-2 text-right">
									{#if c.type === 'retard' || c.statut === 'Retard'}
										<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-amber-600 text-white inline-block">
											Retard
										</span>
									{:else if c.justifie}
										<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white inline-block">
											Justifiée
										</span>
									{:else}
										<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-rose-600 text-white inline-block">
											Injustifiée
										</span>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Volet latéral de détail d'un créneau d'absence -->
	{#if selectedAbsence}
		<div class="fixed inset-0 z-50 flex justify-end">
			<!-- Backdrop sombre pour fermer -->
			<button
				type="button"
				aria-label="Fermer"
				onclick={() => (selectedAbsence = null)}
				class="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity cursor-pointer border-none"
			></button>

			<!-- Panneau tiroir latéral droit -->
			<div
				class="relative w-full max-w-md h-full bg-app-card border-l border-app-border shadow-2xl flex flex-col z-10 overflow-y-auto"
			>
				<!-- En-tête -->
				<div class="flex items-center justify-between p-5 border-b border-app-border">
					<div>
						<h2 class="text-base font-bold text-white">Détail de l'absence</h2>
						<p class="text-xs text-zinc-400 mt-0.5">{formatDateFr(selectedAbsence.date)}</p>
					</div>
					<button
						type="button"
						onclick={() => (selectedAbsence = null)}
						class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors cursor-pointer"
						aria-label="Fermer"
					>
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- Corps -->
				<div class="p-6 space-y-6 flex-1">
					<!-- Badge et titre de la matière -->
					<div class="space-y-2">
						<div>
							{#if selectedAbsence.type === 'retard' || selectedAbsence.statut === 'Retard'}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-amber-600 text-white">
									Retard
								</span>
							{:else if selectedAbsence.justifie}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-emerald-600 text-white">
									Absence Justifiée
								</span>
							{:else}
								<span class="rounded-full px-3 py-1 text-xs font-semibold bg-rose-600 text-white">
									Absence Injustifiée
								</span>
							{/if}
						</div>

						<h3 class="text-lg font-bold text-white leading-snug">
							{selectedAbsence.matiere || "Module non précisé"}
						</h3>
					</div>

					<!-- Carte Informations sur le créneau -->
					<div class="p-4 rounded-xl bg-app-surface border border-app-border space-y-3">
						<div class="flex items-center justify-between text-xs">
							<span class="text-zinc-400 flex items-center gap-1.5">
								<Calendar class="w-4 h-4 text-cyan-400" />
								<span>Date</span>
							</span>
							<span class="font-bold text-white capitalize">
								{formatFullDate(selectedAbsence.date)}
							</span>
						</div>

						<div class="flex items-center justify-between text-xs pt-2 border-t border-white/5">
							<span class="text-zinc-400 flex items-center gap-1.5">
								<Clock class="w-4 h-4 text-cyan-400" />
								<span>Créneau horaire</span>
							</span>
							<span class="font-bold text-white">
								{selectedAbsence.heure_debut} à {selectedAbsence.heure_fin}
							</span>
						</div>

						<div class="flex items-center justify-between text-xs pt-2 border-t border-white/5">
							<span class="text-zinc-400">Durée décomptée</span>
							<span class="font-bold text-white">
								{formatDuration(selectedAbsence.duree_heures)} ({selectedAbsence.duree_heures} h)
							</span>
						</div>

						<div class="flex items-center justify-between text-xs pt-2 border-t border-white/5">
							<span class="text-zinc-400 flex items-center gap-1.5">
								<UserIcon class="w-4 h-4 text-cyan-400" />
								<span>Enseignant</span>
							</span>
							<span class="font-bold text-white">
								{selectedAbsence.enseignant || "Non renseigné"}
							</span>
						</div>
					</div>

					<!-- Démarche administrative / Statut ScoDoc -->
					<div class="p-4 rounded-xl bg-app-surface border border-app-border space-y-2">
						<div class="flex items-center gap-2">
							{#if selectedAbsence.justifie}
								<CheckCircle2 class="w-4 h-4 text-emerald-400" />
								<h4 class="text-xs font-bold text-white uppercase tracking-wider">
									Justificatif validé
								</h4>
							{:else}
								<AlertCircle class="w-4 h-4 text-rose-400" />
								<h4 class="text-xs font-bold text-white uppercase tracking-wider">
									Justificatif en attente ou manquant
								</h4>
							{/if}
						</div>

						<p class="text-xs text-zinc-300 leading-relaxed">
							{#if selectedAbsence.justifie}
								Ce créneau d'absence a été officiellement régularisé sur ScoDoc par l'équipe pédagogique ou le secrétariat.
							{:else}
								Cette absence est comptabilisée comme non justifiée. Conformément au règlement des études du BUT Réseaux & Télécoms, tout certificat médical ou justificatif officiel doit être remis dans un délai de 48 heures au secrétariat de département.
							{/if}
						</p>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
