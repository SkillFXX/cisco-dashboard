<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { auth } from "$lib/stores/auth.svelte";
	import {
		Settings,
		User,
		Mail,
		KeyRound,
		Link2,
		Check,
		AlertCircle,
		FileText,
		BookOpen,
		Calendar,
		ShieldCheck,
		Sparkles,
		RefreshCw
	} from "lucide-svelte";

	// Profile state
	let email = $state(auth.user?.email || "");
	let current_password = $state("");
	let new_password = $state("");
	let isSavingProfile = $state(false);
	let profileSuccessMsg = $state("");
	let profileErrorMsg = $state("");

	// Services state
	let scodoc_url = $state("https://wscodoc.iutbeziers.fr");
	let scodoc_username = $state("");
	let scodoc_password = $state("");
	let scodoc_configured = $state(false);
	let scodoc_verified = $state(false);
	let scodoc_last_error = $state("");

	let moodle_url = $state("https://moodle.umontpellier.fr");
	let moodle_username = $state("");
	let moodle_password = $state("");
	let moodle_token = $state("");
	let moodle_configured = $state(false);
	let moodle_verified = $state(false);
	let moodle_last_error = $state("");

	let ical_url = $state("");
	let ical_configured = $state(false);
	let ical_verified = $state(false);
	let ical_last_error = $state("");

	let testingService = $state<string | null>(null);
	let testFeedback = $state<{ service: string; success: boolean; message: string } | null>(null);

	let isLoading = $state(true);
	let isSavingServices = $state(false);
	let servicesSuccessMsg = $state("");
	let servicesErrorMsg = $state("");

	$effect(() => {
		if (auth.user && auth.user.email) {
			if (!email) email = auth.user.email;
		}
	});

	async function loadSettings() {
		isLoading = true;
		servicesErrorMsg = "";
		try {
			const data = await api.getSettings();
			if (data.scodoc_url) scodoc_url = data.scodoc_url;
			if (data.scodoc_username) scodoc_username = data.scodoc_username;
			scodoc_configured = data.scodoc_configured;
			scodoc_verified = data.scodoc_verified;
			scodoc_last_error = data.scodoc_last_error || "";

			if (data.moodle_url) moodle_url = data.moodle_url;
			if (data.moodle_username) moodle_username = data.moodle_username;
			moodle_configured = data.moodle_configured;
			moodle_verified = data.moodle_verified;
			moodle_last_error = data.moodle_last_error || "";

			if (data.ical_url) ical_url = data.ical_url;
			ical_configured = data.ical_configured;
			ical_verified = data.ical_verified;
			ical_last_error = data.ical_last_error || "";

			if (auth.user) {
				email = auth.user.email || "";
			}
		} catch (e: any) {
			servicesErrorMsg = e.message || "Erreur de chargement des paramètres";
		} finally {
			isLoading = false;
		}
	}

	async function testConnection(service: "scodoc" | "moodle" | "ical") {
		testingService = service;
		testFeedback = null;
		try {
			let payload: any = { service, save_if_valid: true };
			if (service === "scodoc") {
				payload.url = scodoc_url.trim();
				payload.username = scodoc_username.trim();
				payload.password = scodoc_password.trim() || undefined;
			} else if (service === "moodle") {
				payload.url = moodle_url.trim();
				payload.username = moodle_username.trim() || undefined;
				payload.password = moodle_password.trim() || undefined;
				payload.token = moodle_token.trim() || undefined;
			} else if (service === "ical") {
				payload.url = ical_url.trim();
			}

			const res = await api.verifyService(payload);
			testFeedback = {
				service,
				success: res.success,
				message: res.message
			};

			if (res.success) {
				if (service === "scodoc") {
					scodoc_verified = true;
					scodoc_last_error = "";
					scodoc_configured = true;
				} else if (service === "moodle") {
					moodle_verified = true;
					moodle_last_error = "";
					moodle_configured = true;
				} else if (service === "ical") {
					ical_verified = true;
					ical_last_error = "";
					ical_configured = true;
				}
				if (res.student_name && auth.user) {
					auth.user.full_name = res.student_name;
				}
			} else {
				if (service === "scodoc") {
					scodoc_verified = false;
					scodoc_last_error = res.message;
				} else if (service === "moodle") {
					moodle_verified = false;
					moodle_last_error = res.message;
				} else if (service === "ical") {
					ical_verified = false;
					ical_last_error = res.message;
				}
			}
		} catch (e: any) {
			testFeedback = {
				service,
				success: false,
				message: e.message || "Erreur lors du test de connexion."
			};
		} finally {
			testingService = null;
		}
	}

	async function saveProfile(e: SubmitEvent) {
		e.preventDefault();
		isSavingProfile = true;
		profileSuccessMsg = "";
		profileErrorMsg = "";

		try {
			await auth.updateProfile({
				email: email.trim(),
				current_password: current_password.trim() || undefined,
				new_password: new_password.trim() || undefined
			});
			profileSuccessMsg = "Profil mis à jour avec succès.";
			current_password = "";
			new_password = "";
			setTimeout(() => {
				profileSuccessMsg = "";
			}, 4000);
		} catch (err: any) {
			profileErrorMsg = err.message || "Erreur lors de la mise à jour du profil.";
		} finally {
			isSavingProfile = false;
		}
	}

	async function saveServices(e: SubmitEvent) {
		e.preventDefault();
		isSavingServices = true;
		servicesSuccessMsg = "";
		servicesErrorMsg = "";

		try {
			const data = await api.updateSettings({
				scodoc_url,
				scodoc_username: scodoc_username.trim() || undefined,
				scodoc_password: scodoc_password.trim() || undefined,
				moodle_url,
				moodle_username: moodle_username.trim() || undefined,
				moodle_password: moodle_password.trim() || undefined,
				moodle_token: moodle_token.trim() || undefined,
				ical_url: ical_url.trim() || undefined,
				use_mock_fallback: false
			});
			servicesSuccessMsg = "Paramètres de connexion aux services enregistrés avec succès.";
			scodoc_password = "";
			moodle_password = "";

			scodoc_configured = data.scodoc_configured;
			scodoc_verified = data.scodoc_verified;
			scodoc_last_error = data.scodoc_last_error || "";

			moodle_configured = data.moodle_configured;
			moodle_verified = data.moodle_verified;
			moodle_last_error = data.moodle_last_error || "";

			ical_configured = data.ical_configured;
			ical_verified = data.ical_verified;
			ical_last_error = data.ical_last_error || "";

			setTimeout(() => {
				servicesSuccessMsg = "";
			}, 4000);
		} catch (err: any) {
			servicesErrorMsg = err.message || "Erreur lors de la mise à jour des paramètres des services.";
		} finally {
			isSavingServices = false;
		}
	}

	onMount(() => {
		loadSettings();
	});
</script>

<div class="max-w-4xl space-y-8 pb-10">
	<!-- En-tête -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<Settings class="w-5 h-5 text-cyan-400" />
				<span>Paramètres & Profil</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Gérez votre compte et synchronisez vos services universitaires (ScoDoc, Moodle, ADE Campus).
			</p>
		</div>

		<button
			type="button"
			onclick={() => (auth.isOnboardingOpen = true)}
			class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs shrink-0"
		>
			<Sparkles class="w-3.5 h-3.5" />
			<span>Assistant d'intégration</span>
		</button>
	</div>

	{#if isLoading}
		<div class="space-y-6">
			{#each Array(4) as _}
				<Card class="space-y-4 p-5">
					<div class="flex items-center justify-between border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<Skeleton class="w-8 h-8 rounded-lg" />
							<div class="space-y-1">
								<Skeleton class="h-4 w-36" />
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
		<!-- Section 1 : Profil Étudiant & Sécurité -->
		<section class="space-y-4">
			<div class="flex items-center gap-2 pb-1 border-b border-app-border">
				<User class="w-4 h-4 text-cyan-400" />
				<h2 class="text-sm font-bold text-white uppercase tracking-wider">Mon Compte & Profil Étudiant</h2>
			</div>

			<form onsubmit={saveProfile} class="space-y-4">
				{#if profileSuccessMsg}
					<div class="p-3.5 rounded-lg bg-emerald-600/20 text-emerald-300 text-xs font-medium flex items-center gap-2">
						<Check class="w-4 h-4 shrink-0" />
						<span>{profileSuccessMsg}</span>
					</div>
				{/if}

				{#if profileErrorMsg}
					<div class="p-3.5 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
						<AlertCircle class="w-4 h-4 shrink-0" />
						<span>{profileErrorMsg}</span>
					</div>
				{/if}

				<Card class="space-y-4 p-5">
					<div class="flex items-center justify-between border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-cyan-600/20 text-cyan-400 flex items-center justify-center">
								<ShieldCheck class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-white text-sm">Informations Personnelles</h3>
								<p class="text-xs text-zinc-400">Identité détectée et adresse email de votre compte.</p>
							</div>
						</div>
					</div>

					<div class="space-y-3">
						<div class="flex items-center justify-between p-3.5 rounded-xl border border-app-border bg-app-surface/50">
							<div>
								<span class="text-[11px] font-medium text-zinc-400 block">Nom & Prénom</span>
								<span class="text-sm font-bold text-white">
									{auth.user?.full_name || "En attente de synchronisation ScoDoc ou Moodle"}
								</span>
							</div>
							<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold {auth.user?.full_name ? 'bg-emerald-600 text-white' : 'bg-zinc-700 text-white'}">
								{auth.user?.full_name ? "Automatique" : "Non détecté"}
							</span>
						</div>

						<div>
							<label for="p-email" class="block text-xs font-medium text-zinc-400 mb-1">Adresse email du compte</label>
							<input
								id="p-email"
								type="email"
								bind:value={email}
								required
								placeholder="prenom.nom@etu.umontpellier.fr"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>

					<!-- Modification du mot de passe -->
					<div class="pt-3 border-t border-app-border">
						<h4 class="text-xs font-semibold text-zinc-300 mb-2 flex items-center gap-1.5">
							<KeyRound class="w-3.5 h-3.5 text-zinc-500" />
							<span>Changement de mot de passe (optionnel)</span>
						</h4>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="p-curpwd" class="block text-[11px] text-zinc-400 mb-1">Mot de passe actuel</label>
								<input
									id="p-curpwd"
									type="password"
									bind:value={current_password}
									placeholder="••••••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="p-newpwd" class="block text-[11px] text-zinc-400 mb-1">Nouveau mot de passe</label>
								<input
									id="p-newpwd"
									type="password"
									bind:value={new_password}
									placeholder="Minimum 4 caractères"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
					</div>

					<div class="flex justify-end pt-1">
						<Button variant="cisco" type="submit" disabled={isSavingProfile}>
							{isSavingProfile ? "Enregistrement..." : "Enregistrer mon profil"}
						</Button>
					</div>
				</Card>
			</form>
		</section>

		<!-- Section 2 : Connexions aux Services Universitaires -->
		<section class="space-y-4">
			<div class="flex items-center gap-2 pb-1 border-b border-app-border">
				<Link2 class="w-4 h-4 text-cyan-400" />
				<h2 class="text-sm font-bold text-white uppercase tracking-wider">Services Universitaires & Synchronisations</h2>
			</div>

			<form onsubmit={saveServices} class="space-y-5">
				{#if servicesSuccessMsg}
					<div class="p-3.5 rounded-lg bg-emerald-600/20 text-emerald-300 text-xs font-medium flex items-center gap-2">
						<Check class="w-4 h-4 shrink-0" />
						<span>{servicesSuccessMsg}</span>
					</div>
				{/if}

				{#if servicesErrorMsg}
					<div class="p-3.5 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
						<AlertCircle class="w-4 h-4 shrink-0" />
						<span>{servicesErrorMsg}</span>
					</div>
				{/if}

				<!-- Card 1 : ScoDoc -->
				<Card class="space-y-4 p-5">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center shrink-0">
								<FileText class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-white text-sm">ScoDoc (Notes, Moyennes & Absences)</h3>
								<p class="text-xs text-zinc-400">Authentification avec le serveur CAS universitaire.</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0">
							{#if scodoc_verified}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
									Vérifié & Connecté
								</span>
							{:else if scodoc_configured}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-red-600 text-white">
									Identifiants invalides
								</span>
							{:else}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-white">
									Non configuré
								</span>
							{/if}

							<button
								type="button"
								onclick={() => testConnection("scodoc")}
								disabled={testingService === "scodoc" || !scodoc_username}
								class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-200 transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
							>
								{#if testingService === "scodoc"}
									<RefreshCw class="w-3 h-3 animate-spin" />
									<span>Vérification...</span>
								{:else}
									<span>Tester</span>
								{/if}
							</button>
						</div>
					</div>

					{#if testFeedback && testFeedback.service === "scodoc"}
						<div class="p-3 rounded-lg text-xs font-medium flex items-center gap-2 {testFeedback.success ? 'bg-emerald-600/20 text-emerald-300' : 'bg-red-600/20 text-red-300'}">
							{#if testFeedback.success}
								<Check class="w-4 h-4 shrink-0" />
							{:else}
								<AlertCircle class="w-4 h-4 shrink-0" />
							{/if}
							<span>{testFeedback.message}</span>
						</div>
					{/if}

					{#if scodoc_last_error && (!testFeedback || testFeedback.service !== "scodoc")}
						<div class="p-3 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
							<AlertCircle class="w-4 h-4 shrink-0" />
							<span>{scodoc_last_error}</span>
						</div>
					{/if}

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
				<Card class="space-y-4 p-5">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center shrink-0">
								<BookOpen class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-white text-sm">Moodle (Devoirs à rendre & DM)</h3>
								<p class="text-xs text-zinc-400">Récupération automatique des échéances et devoirs à rendre.</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0">
							{#if moodle_verified}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
									Vérifié & Connecté
								</span>
							{:else if moodle_configured}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-red-600 text-white">
									Identifiants invalides
								</span>
							{:else}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-white">
									Non configuré
								</span>
							{/if}

							<button
								type="button"
								onclick={() => testConnection("moodle")}
								disabled={testingService === "moodle" || (!moodle_username && !moodle_token)}
								class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-200 transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
							>
								{#if testingService === "moodle"}
									<RefreshCw class="w-3 h-3 animate-spin" />
									<span>Vérification...</span>
								{:else}
									<span>Tester</span>
								{/if}
							</button>
						</div>
					</div>

					{#if testFeedback && testFeedback.service === "moodle"}
						<div class="p-3 rounded-lg text-xs font-medium flex items-center gap-2 {testFeedback.success ? 'bg-emerald-600/20 text-emerald-300' : 'bg-red-600/20 text-red-300'}">
							{#if testFeedback.success}
								<Check class="w-4 h-4 shrink-0" />
							{:else}
								<AlertCircle class="w-4 h-4 shrink-0" />
							{/if}
							<span>{testFeedback.message}</span>
						</div>
					{/if}

					{#if moodle_last_error && (!testFeedback || testFeedback.service !== "moodle")}
						<div class="p-3 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
							<AlertCircle class="w-4 h-4 shrink-0" />
							<span>{moodle_last_error}</span>
						</div>
					{/if}

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
				<Card class="space-y-4 p-5">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0">
								<Calendar class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-white text-sm">Emploi du Temps ADE Campus (Flux iCal)</h3>
								<p class="text-xs text-zinc-400">Synchronisation des cours, salles, enseignants et créneaux de DS.</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0">
							{#if ical_verified}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
									Vérifié & Connecté
								</span>
							{:else if ical_configured}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-red-600 text-white">
									Flux invalide
								</span>
							{:else}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-white">
									Non configuré
								</span>
							{/if}

							<button
								type="button"
								onclick={() => testConnection("ical")}
								disabled={testingService === "ical" || !ical_url}
								class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-200 transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
							>
								{#if testingService === "ical"}
									<RefreshCw class="w-3 h-3 animate-spin" />
									<span>Vérification...</span>
								{:else}
									<span>Tester</span>
								{/if}
							</button>
						</div>
					</div>

					{#if testFeedback && testFeedback.service === "ical"}
						<div class="p-3 rounded-lg text-xs font-medium flex items-center gap-2 {testFeedback.success ? 'bg-emerald-600/20 text-emerald-300' : 'bg-red-600/20 text-red-300'}">
							{#if testFeedback.success}
								<Check class="w-4 h-4 shrink-0" />
							{:else}
								<AlertCircle class="w-4 h-4 shrink-0" />
							{/if}
							<span>{testFeedback.message}</span>
						</div>
					{/if}

					{#if ical_last_error && (!testFeedback || testFeedback.service !== "ical")}
						<div class="p-3 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
							<AlertCircle class="w-4 h-4 shrink-0" />
							<span>{ical_last_error}</span>
						</div>
					{/if}

					<div>
						<label for="ical-url" class="block text-xs font-medium text-zinc-400 mb-1">Lien de l'URL iCal exporté (.ics)</label>
						<div class="flex items-center gap-2">
							<Link2 class="w-4 h-4 text-zinc-500 shrink-0" />
							<input
								id="ical-url"
								type="url"
								bind:value={ical_url}
								placeholder="https://edt.umontpellier.fr/.../export.ics"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>
				</Card>

				<div class="flex justify-end gap-3 pt-2">
					<Button variant="cisco" type="submit" size="lg" disabled={isSavingServices}>
						{isSavingServices ? "Enregistrement..." : "Enregistrer les Services"}
					</Button>
				</div>
			</form>
		</section>
	{/if}
</div>
