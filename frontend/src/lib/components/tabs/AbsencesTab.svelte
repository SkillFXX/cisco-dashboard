<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Badge from "../Badge.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { Clock, AlertTriangle, CheckCircle, RefreshCw } from "lucide-svelte";

	let absencesData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");

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
	});
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<Clock class="w-5 h-5 text-cyan-400" />
				<span>Bilan d'Assiduité & Absences</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Données extraites en temps réel de votre compte ScoDoc. Suivi des justificatifs et des heures manquées.
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

	{#if isLoading}
		<div class="flex flex-col items-center justify-center p-12 text-zinc-400">
			<RefreshCw class="w-7 h-7 animate-spin text-cyan-400 mb-3" />
			<p class="text-xs">Synchronisation des absences avec ScoDoc...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
			{error}
		</div>
	{:else if absencesData}
		<!-- 3 Summary KPI Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
			<!-- Absences Injustifiées -->
			<Card class="relative overflow-hidden">
				<div class="flex items-center justify-between mb-2">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Absences Injustifiées</span>
					<div class="w-8 h-8 rounded-lg bg-red-600/20 text-red-400 flex items-center justify-center">
						<AlertTriangle class="w-4 h-4" />
					</div>
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-black {absencesData.injustifiees_nb > 0 ? 'text-rose-400' : 'text-emerald-400'}">
						{absencesData.injustifiees_nb}
					</span>
					<span class="text-xs text-zinc-400">
						créneau{absencesData.injustifiees_nb > 1 ? 'x' : ''} ({absencesData.injustifiees_heures}h)
					</span>
				</div>
				<p class="text-xs text-zinc-500 mt-2">
					{absencesData.injustifiees_nb > 0 ? "Pensez à transmettre vos justificatifs au secrétariat de département." : "Aucune absence injustifiée constatée."}
				</p>
			</Card>

			<!-- Absences Justifiées -->
			<Card class="relative overflow-hidden">
				<div class="flex items-center justify-between mb-2">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Absences Justifiées</span>
					<div class="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center">
						<CheckCircle class="w-4 h-4" />
					</div>
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-black text-emerald-400">
						{absencesData.justifiees_nb}
					</span>
					<span class="text-xs text-zinc-400">
						créneau{absencesData.justifiees_nb > 1 ? 'x' : ''} ({absencesData.justifiees_heures}h)
					</span>
				</div>
				<p class="text-xs text-zinc-500 mt-2">
					Justificatifs validés par les enseignants et l'administration.
				</p>
			</Card>

			<!-- Retards & Total -->
			<Card class="relative overflow-hidden">
				<div class="flex items-center justify-between mb-2">
					<span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Retards & Cumul</span>
					<div class="w-8 h-8 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center">
						<Clock class="w-4 h-4" />
					</div>
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-black text-white">
						{absencesData.retards_nb}
					</span>
					<span class="text-xs text-zinc-400">retard{absencesData.retards_nb > 1 ? 's' : ''}</span>
				</div>
				<p class="text-xs text-zinc-500 mt-2">
					Total cumulé de la scolarité : {absencesData.total_heures} heures ({absencesData.total_nb} créneaux)
				</p>
			</Card>
		</div>

		<!-- Créneaux détaillés -->
		<Card>
			<h2 class="text-sm font-bold text-white mb-4">Historique Chronologique des Créneaux</h2>

			<div class="space-y-3">
				{#if !absencesData.creneaux || absencesData.creneaux.length === 0}
					<p class="text-xs text-zinc-500 text-center py-8">
						Félicitations ! Aucune absence enregistrée sur ScoDoc ce semestre.
					</p>
				{:else}
					{#each absencesData.creneaux as c}
						<div class="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-lg border border-app-border bg-app-surface hover:border-zinc-700 transition-colors gap-3">
							<div class="space-y-1">
								<div class="flex items-center gap-2">
									<Badge variant={c.justifie ? 'success' : 'destructive'}>
										{c.justifie ? 'Justifiée' : 'Injustifiée'}
									</Badge>
									<span class="font-bold text-sm text-white">{c.matiere}</span>
								</div>

								<div class="text-xs text-zinc-400 flex items-center gap-2">
									<span>Le {c.date} ({c.heure_debut} - {c.heure_fin})</span>
									<span>•</span>
									<span class="font-medium text-cyan-400">{c.duree_heures}h</span>
									{#if c.enseignant}
										<span>•</span>
										<span class="text-zinc-500">{c.enseignant}</span>
									{/if}
								</div>
							</div>

							<div class="text-left sm:text-right shrink-0">
								<span class="text-xs font-medium text-zinc-400">
									{c.statut}
								</span>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</Card>
	{/if}
</div>
