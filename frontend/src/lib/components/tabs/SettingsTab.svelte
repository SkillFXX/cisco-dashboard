<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import Badge from "../Badge.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { Settings, Link2, Check, RefreshCw, AlertCircle, FileText, BookOpen, Calendar } from "lucide-svelte";

	let scodoc_url = $state("https://wscodoc.iutbeziers.fr");
	let scodoc_username = $state("");
	let scodoc_password = $state("");

	let moodle_url = $state("https://moodle.umontpellier.fr");
	let moodle_username = $state("");
	let moodle_password = $state("");
	let moodle_token = $state("");

	let ical_url = $state("");

	let isLoading = $state(true);
	let isSaving = $state(false);
	let successMsg = $state("");
	let errorMsg = $state("");

	async function loadSettings() {
		isLoading = true;
		errorMsg = "";
		try {
			const data = await api.getSettings();
			if (data.scodoc_url) scodoc_url = data.scodoc_url;
			if (data.scodoc_username) scodoc_username = data.scodoc_username;
			if (data.moodle_url) moodle_url = data.moodle_url;
			if (data.moodle_username) moodle_username = data.moodle_username;
			if (data.ical_url) ical_url = data.ical_url;
		} catch (e: any) {
			errorMsg = e.message || "Erreur de chargement des paramètres";
		} finally {
			isLoading = false;
		}
	}

	async function saveSettings(e: SubmitEvent) {
		e.preventDefault();
		isSaving = true;
		successMsg = "";
		errorMsg = "";

		try {
			await api.updateSettings({
				scodoc_url,
				scodoc_username,
				scodoc_password: scodoc_password.trim() || undefined,
				moodle_url,
				moodle_username,
				moodle_password: moodle_password.trim() || undefined,
				moodle_token: moodle_token.trim() || undefined,
				ical_url: ical_url.trim() || undefined,
				use_mock_fallback: false
			});
			successMsg = "Paramètres et identifiants enregistrés avec succès !";
			scodoc_password = "";
			moodle_password = "";
			setTimeout(() => {
				successMsg = "";
			}, 4000);
		} catch (err: any) {
			errorMsg = err.message || "Erreur lors de la mise à jour des paramètres.";
		} finally {
			isSaving = false;
		}
	}

	onMount(() => {
		loadSettings();
	});
</script>

<div class="max-w-4xl space-y-6">
	<!-- Header -->
	<div class="pb-2 border-b border-app-border">
		<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
			<Settings class="w-5 h-5 text-cyan-400" />
			<span>Gestion des Services & Connexions</span>
		</h1>
		<p class="text-xs text-zinc-400 mt-0.5">
			Renseignez vos accès à ScoDoc, Moodle et votre lien de calendrier ADE Campus pour synchroniser automatiquement vos notes, devoirs et cours réels.
		</p>
	</div>

	{#if isLoading}
		<div class="space-y-6">
			{#each Array(3) as _}
				<Card class="space-y-4 p-5">
					<div class="flex items-center justify-between border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<Skeleton class="w-8 h-8 rounded-lg" />
							<div class="space-y-1">
								<Skeleton class="h-4 w-32" />
								<Skeleton class="h-3 w-48" />
							</div>
						</div>
						<Skeleton class="h-5 w-20 rounded-full" />
					</div>
					<div class="space-y-3 pt-1">
						<Skeleton class="h-9 w-full rounded-lg" />
						<Skeleton class="h-9 w-full rounded-lg" />
					</div>
				</Card>
			{/each}
		</div>
	{:else}
		<form onsubmit={saveSettings} class="space-y-6">
			{#if successMsg}
				<div class="p-3.5 rounded-lg bg-emerald-600/20 text-emerald-300 text-xs font-medium flex items-center gap-2">
					<Check class="w-4 h-4 shrink-0" />
					<span>{successMsg}</span>
				</div>
			{/if}

			{#if errorMsg}
				<div class="p-3.5 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
					<AlertCircle class="w-4 h-4 shrink-0" />
					<span>{errorMsg}</span>
				</div>
			{/if}

			<!-- Card 1 : ScoDoc -->
			<Card class="space-y-4">
				<div class="flex items-center justify-between border-b border-app-border pb-3">
					<div class="flex items-center gap-2.5">
						<div class="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center">
							<FileText class="w-4 h-4" />
						</div>
						<div>
							<h3 class="font-bold text-white text-sm">ScoDoc (Notes, Moyennes & Absences)</h3>
							<p class="text-xs text-zinc-400">Authentification automatique avec le serveur CAS universitaire.</p>
						</div>
					</div>
					<Badge variant={scodoc_username ? "success" : "outline"}>
						{scodoc_username ? "Compte configuré" : "Non configuré"}
					</Badge>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
					<div>
						<label for="scodoc-url" class="block text-xs font-medium text-zinc-400 mb-1">URL du serveur ScoDoc</label>
						<input
							id="scodoc-url"
							type="text"
							bind:value={scodoc_url}
							placeholder="https://wscodoc.iutbeziers.fr"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
					<div>
						<label for="scodoc-user" class="block text-xs font-medium text-zinc-400 mb-1">Identifiant CAS ENT</label>
						<input
							id="scodoc-user"
							type="text"
							bind:value={scodoc_username}
							placeholder="prenom.nom"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
					<div>
						<label for="scodoc-pwd" class="block text-xs font-medium text-zinc-400 mb-1">Mot de passe CAS</label>
						<input
							id="scodoc-pwd"
							type="password"
							bind:value={scodoc_password}
							placeholder="••••••••••••"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
				</div>
			</Card>

			<!-- Card 2 : Moodle -->
			<Card class="space-y-4">
				<div class="flex items-center justify-between border-b border-app-border pb-3">
					<div class="flex items-center gap-2.5">
						<div class="w-8 h-8 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center">
							<BookOpen class="w-4 h-4" />
						</div>
						<div>
							<h3 class="font-bold text-white text-sm">Moodle (Devoirs à rendre & Cours)</h3>
							<p class="text-xs text-zinc-400">Récupération des échéances de devoirs et travaux pratiques.</p>
						</div>
					</div>
					<Badge variant={moodle_username || moodle_token ? "success" : "outline"}>
						{moodle_username || moodle_token ? "Compte configuré" : "Non configuré"}
					</Badge>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
					<div>
						<label for="moodle-url" class="block text-xs font-medium text-zinc-400 mb-1">URL de votre Moodle</label>
						<input
							id="moodle-url"
							type="text"
							bind:value={moodle_url}
							placeholder="https://moodle.umontpellier.fr"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
					<div>
						<label for="moodle-user" class="block text-xs font-medium text-zinc-400 mb-1">Identifiant Moodle</label>
						<input
							id="moodle-user"
							type="text"
							bind:value={moodle_username}
							placeholder="prenom.nom"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
					<div>
						<label for="moodle-pwd" class="block text-xs font-medium text-zinc-400 mb-1">Mot de passe Moodle</label>
						<input
							id="moodle-pwd"
							type="password"
							bind:value={moodle_password}
							placeholder="••••••••••••"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
				</div>

				<div class="pt-2">
					<label for="moodle-token" class="block text-xs font-medium text-zinc-400 mb-1">
						Ou Jeton WebService personnel (optionnel)
					</label>
					<input
						id="moodle-token"
						type="text"
						bind:value={moodle_token}
						placeholder="Ex: 8f9b4c2e1a3d5e7f9a0b1c2d3e4f5a6b"
						class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
					/>
				</div>
			</Card>

			<!-- Card 3 : ADE Campus / UM Net iCal -->
			<Card class="space-y-4">
				<div class="flex items-center justify-between border-b border-app-border pb-3">
					<div class="flex items-center gap-2.5">
						<div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
							<Calendar class="w-4 h-4" />
						</div>
						<div>
							<h3 class="font-bold text-white text-sm">Emploi du Temps UM Montpellier (Flux iCal)</h3>
							<p class="text-xs text-zinc-400">Collez le lien iCal exporté depuis ADE Campus / UM Net.</p>
						</div>
					</div>
					<Badge variant={ical_url ? "success" : "outline"}>
						{ical_url ? "Lien iCal configuré" : "Non configuré"}
					</Badge>
				</div>

				<div>
					<label for="ical-url" class="block text-xs font-medium text-zinc-400 mb-1">Lien de l'URL iCal (.ics)</label>
					<div class="flex items-center gap-2">
						<Link2 class="w-4 h-4 text-zinc-500 shrink-0" />
						<input
							id="ical-url"
							type="url"
							bind:value={ical_url}
							placeholder="https://edt.umontpellier.fr/ade/custom/modules/Views/fetch.jsp?data=... ou fichier .ics"
							class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
						/>
					</div>
				</div>
			</Card>

			<div class="flex justify-end gap-3 pt-2">
				<Button variant="cisco" type="submit" size="lg" disabled={isSaving}>
					{isSaving ? "Enregistrement..." : "Enregistrer les Accès"}
				</Button>
			</div>
		</form>
	{/if}
</div>
