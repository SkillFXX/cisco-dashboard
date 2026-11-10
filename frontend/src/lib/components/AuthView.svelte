<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import Card from "./Card.svelte";
	import Button from "./Button.svelte";
	import Badge from "./Badge.svelte";
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { ArrowRight, Mail, Lock } from "lucide-svelte";

	let mode = $state<"login" | "register" | "forgot" | "reset">("login");
	let canResetPassword = $state(false);
	let resetToken = $state("");
	let forgotEmail = $state("");
	let newPassword = $state("");
	let info = $state("");

	onMount(async () => {
		const token = new URLSearchParams(window.location.search).get("reset");
		if (token) {
			resetToken = token;
			mode = "reset";
		}
		try {
			canResetPassword = (await api.getCapabilities()).password_reset;
		} catch {
			canResetPassword = false;
		}
	});

	async function handleForgot(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		info = "";
		try {
			info = (await api.forgotPassword(forgotEmail)).message;
		} catch (err: any) {
			error = err.message || "Impossible d'envoyer l'email.";
		} finally {
			isSubmitting = false;
		}
	}

	async function handleReset(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		try {
			info = (await api.resetPassword(resetToken, newPassword)).message;
			newPassword = "";
			resetToken = "";
			window.history.replaceState({}, "", window.location.pathname);
			mode = "login";
		} catch (err: any) {
			error = err.message || "Lien invalide ou expiré.";
		} finally {
			isSubmitting = false;
		}
	}

	// Login state
	let loginEmail = $state("");
	let loginPassword = $state("");

	// Register state
	let regEmail = $state("");
	let regPassword = $state("");

	let isSubmitting = $state(false);
	let error = $state("");

	async function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		try {
			await auth.login(loginEmail, loginPassword);
		} catch (err: any) {
			error = err.message || "Adresse email ou mot de passe incorrect";
		} finally {
			isSubmitting = false;
		}
	}

	async function handleRegister(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		try {
			await auth.register({
				email: regEmail,
				password: regPassword
			});
		} catch (err: any) {
			error = err.message || "Erreur lors de la création du compte";
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="min-h-screen flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-app-bg text-fg font-sans">
	<div class="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
		<div class="inline-flex items-center justify-center">
			<img src="/icon.png" alt="Cisco" class="w-16 h-16 rounded-xl object-contain shadow-2xl" />
		</div>
		<h1 class="text-3xl font-extrabold tracking-tight text-fg">
			CISCO DASHBOARD
		</h1>
		<p class="text-sm text-muted">
			Le tableau de bord unifié pour étudiants en <strong>BUT Réseaux & Télécoms</strong>
		</p>
		<div class="flex items-center justify-center gap-2 pt-1">
			<Badge variant="cisco">ScoDoc</Badge>
			<Badge variant="secondary">Moodle</Badge>
			<Badge variant="outline">Emploi du temps</Badge>
		</div>
	</div>

	<div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
		<Card class="p-6 sm:p-8 border-app-border bg-app-card shadow-2xl rounded-xl">
			<!-- Tab Switcher -->
			{#if mode === "login" || mode === "register"}
			<div class="grid grid-cols-2 p-1 bg-app-surface rounded-lg mb-6 border border-app-border">
				<button
					type="button"
					onclick={() => { mode = "login"; error = ""; }}
					class="py-2 text-xs font-semibold rounded-md transition-all cursor-pointer {mode === 'login' ? 'bg-fg/[0.08] text-fg shadow-xs' : 'text-muted hover:text-fg'}"
				>
					Se connecter
				</button>
				<button
					type="button"
					onclick={() => { mode = "register"; error = ""; }}
					class="py-2 text-xs font-semibold rounded-md transition-all cursor-pointer {mode === 'register' ? 'bg-fg/[0.08] text-fg shadow-xs' : 'text-muted hover:text-fg'}"
				>
					Créer un compte
				</button>
			</div>
			{/if}

			{#if info}
				<div class="p-3 mb-5 rounded-lg bg-emerald-600/20 text-emerald-300 text-xs font-medium">
					{info}
				</div>
			{/if}

			{#if error}
				<div class="p-3 mb-5 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
					{error}
				</div>
			{/if}

			{#if mode === "login"}
				<!-- Formulaire Connexion -->
				<form onsubmit={handleLogin} class="space-y-4">
					<div>
						<label for="l-email" class="block text-xs font-medium text-muted mb-1">Adresse email</label>
						<div class="relative">
							<Mail class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
							<input
								id="l-email"
								type="email"
								bind:value={loginEmail}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
								placeholder="votre.email@etu.umontpellier.fr"
							/>
						</div>
					</div>

					<div>
						<label for="l-pwd" class="block text-xs font-medium text-muted mb-1">Mot de passe</label>
						<div class="relative">
							<Lock class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
							<input
								id="l-pwd"
								type="password"
								bind:value={loginPassword}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
								placeholder="••••••••••••"
							/>
						</div>
					</div>

					<Button variant="cisco" type="submit" class="w-full" disabled={isSubmitting}>
						{isSubmitting ? "Connexion en cours..." : "Accéder à mon Dashboard"}
						<ArrowRight class="w-4 h-4" />
					</Button>
					{#if canResetPassword}
						<button
							type="button"
							onclick={() => { mode = "forgot"; error = ""; info = ""; }}
							class="w-full text-center text-xs text-muted hover:text-cyan-400 transition-colors cursor-pointer"
						>
							Mot de passe oublié ?
						</button>
					{/if}
				</form>
			{:else if mode === "register"}
				<!-- Formulaire Inscription minimaliste (Email + Mot de passe uniquement) -->
				<form onsubmit={handleRegister} class="space-y-4">
					<div>
						<label for="r-email" class="block text-xs font-medium text-muted mb-1">Adresse email</label>
						<div class="relative">
							<Mail class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
							<input
								id="r-email"
								type="email"
								bind:value={regEmail}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
								placeholder="votre.email@etu.umontpellier.fr"
							/>
						</div>
					</div>

					<div>
						<label for="r-pwd" class="block text-xs font-medium text-muted mb-1">Mot de passe</label>
						<div class="relative">
							<Lock class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
							<input
								id="r-pwd"
								type="password"
								bind:value={regPassword}
								required
								minlength="8"
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
								placeholder="••••••••••••"
							/>
						</div>
					</div>

					<p class="text-[11px] text-muted leading-relaxed pt-1">
						Votre nom, prénom et accès aux services (ScoDoc, Moodle, ADE) pourront être configurés ou modifiés à tout moment dans les Paramètres.
					</p>

					<Button variant="cisco" type="submit" class="w-full mt-2" disabled={isSubmitting}>
						{isSubmitting ? "Création en cours..." : "Créer mon Compte"}
						<ArrowRight class="w-4 h-4" />
					</Button>
				</form>
			{:else if mode === "forgot"}
				<form onsubmit={handleForgot} class="space-y-4">
					<p class="text-xs text-muted leading-relaxed">
						Saisissez l'adresse email de votre compte : un lien de réinitialisation vous sera envoyé.
					</p>
					<div class="relative">
						<Mail class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
						<input
							type="email"
							bind:value={forgotEmail}
							required
							aria-label="Adresse email"
							class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							placeholder="votre.email@etu.umontpellier.fr"
						/>
					</div>
					<Button variant="cisco" type="submit" class="w-full" disabled={isSubmitting}>
						{isSubmitting ? "Envoi..." : "Envoyer le lien"}
					</Button>
					<button type="button" onclick={() => { mode = "login"; error = ""; info = ""; }} class="w-full text-center text-xs text-muted hover:text-fg cursor-pointer">
						Retour à la connexion
					</button>
				</form>
			{:else if mode === "reset"}
				<form onsubmit={handleReset} class="space-y-4">
					<p class="text-xs text-muted leading-relaxed">Choisissez votre nouveau mot de passe (8 caractères minimum).</p>
					<div class="relative">
						<Lock class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
						<input
							type="password"
							bind:value={newPassword}
							required
							minlength="8"
							aria-label="Nouveau mot de passe"
							class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							placeholder="Nouveau mot de passe"
						/>
					</div>
					<Button variant="cisco" type="submit" class="w-full" disabled={isSubmitting}>
						{isSubmitting ? "Enregistrement..." : "Changer mon mot de passe"}
					</Button>
				</form>
			{/if}
		</Card>
	</div>
</div>
