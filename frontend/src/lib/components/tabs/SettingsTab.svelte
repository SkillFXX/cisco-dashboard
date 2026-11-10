<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import Button from "../Button.svelte";
	import ThemeToggle from "../ThemeToggle.svelte";
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
		Palette,
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

	let moodle_url = $state("https://moodle-but.iutbeziers.fr/moodle");
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

	function statusOf(verified: boolean, configured: boolean, error: string) {
		if (verified) return { label: "Connecté", cls: "bg-emerald-600/15 text-emerald-400" };
		if (configured && error) return { label: "Erreur", cls: "bg-red-600/15 text-red-400" };
		if (configured) return { label: "À vérifier", cls: "bg-amber-600/15 text-amber-400" };
		return { label: "Non configuré", cls: "bg-app-raised text-muted" };
	}

	let serviceStatuses = $derived([
		{ id: "scodoc", name: "ScoDoc", ...statusOf(scodoc_verified, scodoc_configured, scodoc_last_error) },
		{ id: "moodle", name: "Moodle", ...statusOf(moodle_verified, moodle_configured, moodle_last_error) },
		{ id: "ical", name: "Emploi du temps", ...statusOf(ical_verified, ical_configured, ical_last_error) }
	]);
	let connectedCount = $derived(serviceStatuses.filter((x) => x.label === "Connecté").length);

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

{#snippet feedback(service: string, lastError: string)}
	{#if testFeedback && testFeedback.service === service}
		<div class="p-3 rounded-lg text-xs font-medium flex items-center gap-2 {testFeedback.success ? 'bg-emerald-600/20 text-emerald-300' : 'bg-red-600/20 text-red-300'}">
			{#if testFeedback.success}
				<Check class="w-4 h-4 shrink-0" />
			{:else}
				<AlertCircle class="w-4 h-4 shrink-0" />
			{/if}
			<span>{testFeedback.message}</span>
		</div>
	{:else if lastError}
		<div class="p-3 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
			<AlertCircle class="w-4 h-4 shrink-0" />
			<span>{lastError}</span>
		</div>
	{/if}
{/snippet}

<div class="max-w-4xl space-y-8 pb-10">
	<!-- En-tête -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-fg">Paramètres</h1>
		</div>

		<button
			type="button"
			onclick={() => (auth.isOnboardingOpen = true)}
			class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs shrink-0"
		>
			<Sparkles class="w-3.5 h-3.5" />
			<span>Assistant de configuration</span>
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
		<!-- Apparence -->
		<section class="space-y-3">
			<div class="flex items-center gap-2 pb-1 border-b border-app-border">
				<Palette class="w-4 h-4 text-cyan-400" />
				<h2 class="text-sm font-bold text-fg uppercase tracking-wider">Apparence</h2>
			</div>
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
				<p class="text-xs text-muted">Thème de l'interface. « Automatique » suit le réglage de votre appareil.</p>
				<ThemeToggle />
			</div>
		</section>

		<!-- Section 1 : Mon compte -->
		<section class="space-y-4">
			<div class="flex items-center gap-2 pb-1 border-b border-app-border">
				<User class="w-4 h-4 text-cyan-400" />
				<h2 class="text-sm font-bold text-fg uppercase tracking-wider">Mon compte</h2>
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
								<h3 class="font-bold text-fg text-sm">Profil</h3>
								<p class="text-xs text-muted">Identité et adresse email</p>
							</div>
						</div>
					</div>

					<div class="space-y-3">
						<div class="flex items-center justify-between">
							<div>
								<span class="text-[11px] font-medium text-muted block">Nom & Prénom</span>
								<span class="text-sm font-bold text-fg">
									{auth.user?.full_name || "En attente de synchronisation"}
								</span>
							</div>
							<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold {auth.user?.full_name ? 'bg-emerald-600/15 text-emerald-400' : 'bg-app-raised text-muted'}">
								{auth.user?.full_name ? "Automatique" : "Non détecté"}
							</span>
						</div>

						<div>
							<label for="p-email" class="block text-xs font-medium text-muted mb-1">Adresse email du compte</label>
							<input
								id="p-email"
								type="email"
								bind:value={email}
								required
								placeholder="prenom.nom@etu.umontpellier.fr"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>

					<!-- Modification du mot de passe -->
					<div class="pt-3 border-t border-app-border">
						<h4 class="text-xs font-semibold text-muted mb-2 flex items-center gap-1.5">
							<KeyRound class="w-3.5 h-3.5 text-subtle" />
							<span>Changement de mot de passe (optionnel)</span>
						</h4>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="p-curpwd" class="block text-[11px] text-muted mb-1">Mot de passe actuel</label>
								<input
									id="p-curpwd"
									type="password"
									bind:value={current_password}
									placeholder="••••••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="p-newpwd" class="block text-[11px] text-muted mb-1">Nouveau mot de passe</label>
								<input
									id="p-newpwd"
									type="password"
									bind:value={new_password}
									placeholder="Minimum 8 caractères"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
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

		<!-- Section 2 : Services -->
		<section class="space-y-4">
			<div class="flex items-center gap-2 pb-1 border-b border-app-border">
				<Link2 class="w-4 h-4 text-cyan-400" />
				<h2 class="text-sm font-bold text-fg uppercase tracking-wider">Services</h2>
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

				<!-- Résumé : état des trois services -->
				<div class="flex flex-wrap items-center gap-2 text-xs">
					<span class="text-muted mr-1"><strong class="text-fg">{connectedCount}</strong> service{connectedCount > 1 ? "s" : ""} sur 3 connecté{connectedCount > 1 ? "s" : ""}</span>
					{#each serviceStatuses as svc}
						<a href="#service-{svc.id}" class="inline-flex items-center gap-1.5 rounded-full border border-app-border bg-app-surface px-2.5 py-1 text-[11px] text-muted hover:text-fg">
							<span class="w-1.5 h-1.5 rounded-full {svc.label === 'Connecté' ? 'bg-emerald-500' : svc.label === 'Erreur' ? 'bg-red-500' : svc.label === 'À vérifier' ? 'bg-amber-500' : 'bg-app-raised2'}"></span>
							{svc.name}
						</a>
					{/each}
				</div>

				<!-- Carte ScoDoc -->
				<Card class="space-y-4 p-5" id="service-scodoc">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center shrink-0">
								<FileText class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-fg text-sm">ScoDoc</h3>
								<p class="text-xs text-muted">Notes, moyennes & absences</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0">
							<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold {statusOf(scodoc_verified, scodoc_configured, scodoc_last_error).cls}">
								{statusOf(scodoc_verified, scodoc_configured, scodoc_last_error).label}
							</span>
							<button
								type="button"
								onclick={() => testConnection("scodoc")}
								disabled={testingService === "scodoc" || !scodoc_username}
								title="Teste la connexion et l'enregistre si elle fonctionne"
								class="px-2.5 py-1 rounded-lg bg-app-raised hover:bg-app-raised2 text-xs font-medium text-fg transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
							>
								{#if testingService === "scodoc"}
									<RefreshCw class="w-3 h-3 animate-spin" />
									<span>Vérification...</span>
								{:else}
									<span>Vérifier & enregistrer</span>
								{/if}
							</button>
						</div>
					</div>

					<p class="text-[11px] leading-relaxed text-subtle">Utilisez les mêmes identifiants que pour votre ENT (compte CAS de l'université). Ils sont chiffrés sur le serveur et servent uniquement à récupérer vos notes.</p>

					{@render feedback("scodoc", scodoc_last_error)}

					<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
						<div>
							<label for="scodoc-url" class="block text-xs font-medium text-muted mb-1">URL de ScoDoc</label>
							<input
								id="scodoc-url"
								type="text"
								bind:value={scodoc_url}
								placeholder="https://wscodoc.iutbeziers.fr"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
						<div>
							<label for="scodoc-user" class="block text-xs font-medium text-muted mb-1">Identifiant CAS</label>
							<input
								id="scodoc-user"
								type="text"
								bind:value={scodoc_username}
								placeholder="prenom.nom"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
						<div>
							<label for="scodoc-pwd" class="block text-xs font-medium text-muted mb-1">Mot de passe CAS</label>
							<input
								id="scodoc-pwd"
								type="password"
								bind:value={scodoc_password}
								placeholder={scodoc_configured ? "Enregistré — laisser vide pour le conserver" : "••••••••••••"}
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>
				</Card>

				<!-- Carte Moodle -->
				<Card class="space-y-4 p-5" id="service-moodle">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center shrink-0">
								<BookOpen class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-fg text-sm">Moodle</h3>
								<p class="text-xs text-muted">Devoirs et cours en ligne</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0">
							<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold {statusOf(moodle_verified, moodle_configured, moodle_last_error).cls}">
								{statusOf(moodle_verified, moodle_configured, moodle_last_error).label}
							</span>
							<button
								type="button"
								onclick={() => testConnection("moodle")}
								disabled={testingService === "moodle" || (!moodle_username && !moodle_token)}
								title="Teste la connexion et l'enregistre si elle fonctionne"
								class="px-2.5 py-1 rounded-lg bg-app-raised hover:bg-app-raised2 text-xs font-medium text-fg transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
							>
								{#if testingService === "moodle"}
									<RefreshCw class="w-3 h-3 animate-spin" />
									<span>Vérification...</span>
								{:else}
									<span>Vérifier & enregistrer</span>
								{/if}
							</button>
						</div>
					</div>

					<p class="text-[11px] leading-relaxed text-subtle">Identifiant et mot de passe de votre compte Moodle. Le jeton personnel est une alternative facultative, à utiliser si la connexion par mot de passe ne fonctionne pas.</p>

					{@render feedback("moodle", moodle_last_error)}

					<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
						<div>
							<label for="moodle-url" class="block text-xs font-medium text-muted mb-1">URL de Moodle</label>
							<input
								id="moodle-url"
								type="text"
								bind:value={moodle_url}
								placeholder="https://moodle-but.iutbeziers.fr/moodle"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
						<div>
							<label for="moodle-user" class="block text-xs font-medium text-muted mb-1">Identifiant Moodle</label>
							<input
								id="moodle-user"
								type="text"
								bind:value={moodle_username}
								placeholder="prenom.nom"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
						<div>
							<label for="moodle-pwd" class="block text-xs font-medium text-muted mb-1">Mot de passe Moodle</label>
							<input
								id="moodle-pwd"
								type="password"
								bind:value={moodle_password}
								placeholder={moodle_configured ? "Enregistré — laisser vide pour le conserver" : "••••••••••••"}
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>

					<details class="group">
						<summary class="text-xs font-medium text-muted hover:text-fg cursor-pointer select-none">
							Avancé : utiliser un jeton personnel
						</summary>
						<div class="pt-2 space-y-1">
							<input
								id="moodle-token"
								type="text"
								bind:value={moodle_token}
								aria-label="Jeton personnel Moodle"
								placeholder="Ex: 8f9b4c2e1a3d5e7f9a0b1c2d3e4f5a6b"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
							<p class="text-[11px] text-subtle">Sur Moodle : Préférences › Clés de sécurité › « Moodle mobile web service ».</p>
						</div>
					</details>
				</Card>

				<!-- Carte Emploi du temps -->
				<Card class="space-y-4 p-5" id="service-ical">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
						<div class="flex items-center gap-2.5">
							<div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0">
								<Calendar class="w-4 h-4" />
							</div>
							<div>
								<h3 class="font-bold text-fg text-sm">Emploi du temps</h3>
								<p class="text-xs text-muted">Planning des cours et évaluations</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0">
							<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold {statusOf(ical_verified, ical_configured, ical_last_error).cls}">
								{statusOf(ical_verified, ical_configured, ical_last_error).label}
							</span>
							<button
								type="button"
								onclick={() => testConnection("ical")}
								disabled={testingService === "ical" || !ical_url}
								title="Teste la connexion et l'enregistre si elle fonctionne"
								class="px-2.5 py-1 rounded-lg bg-app-raised hover:bg-app-raised2 text-xs font-medium text-fg transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
							>
								{#if testingService === "ical"}
									<RefreshCw class="w-3 h-3 animate-spin" />
									<span>Vérification...</span>
								{:else}
									<span>Vérifier & enregistrer</span>
								{/if}
							</button>
						</div>
					</div>

					<p class="text-[11px] leading-relaxed text-subtle">Dans ADE Campus / UM Net, exportez votre planning au format iCal (.ics) puis collez ici le lien obtenu.</p>

					{@render feedback("ical", ical_last_error)}

					<div>
						<label for="ical-url" class="block text-xs font-medium text-muted mb-1">Lien iCal (.ics)</label>
						<div class="flex items-center gap-2">
							<Link2 class="w-4 h-4 text-subtle shrink-0" />
							<input
								id="ical-url"
								type="url"
								bind:value={ical_url}
								placeholder="https://edt.umontpellier.fr/.../export.ics"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>
				</Card>

				<div class="flex justify-end gap-3 pt-2">
					<Button variant="cisco" type="submit" size="lg" disabled={isSavingServices}>
						{isSavingServices ? "Enregistrement..." : "Enregistrer les services"}
					</Button>
				</div>
			</form>
		</section>
	{/if}
</div>
