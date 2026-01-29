<script lang="ts">
	import type { FileNode } from "./types";
	import { createEventDispatcher } from "svelte";

	import Arrow from "./ArrowIcon.svelte";
	import Checkbox from "./Checkbox.svelte";
	import FileIcon from "../icons/light-file.svg";

	export let path: string[] = [];
	export let selected: string[][] = [];
	export let is_selected_entirely = false;
	export let interactive: boolean;
	export let ls_fn: (path: string[]) => Promise<FileNode[]>;
	export let file_count: "single" | "multiple" = "multiple";
	export let valid_for_selection: boolean;

	let content: FileNode[] = [];
	let opened_folders: number[] = [];

	const toggle_open_folder = (i: number): void => {
		if (opened_folders.includes(i)) {
			opened_folders = opened_folders.filter((x) => x !== i);
		} else {
			opened_folders = [...opened_folders, i];
		}
	};

	const path_next_to = (path: string[], path_2: string[]): boolean => {
		return path.join("/").startsWith(path_2.slice(0, -1).join("/")) && path.length === path_2.length;
	};


	(async () => {
		content = await ls_fn(path);
		if (valid_for_selection && file_count === "multiple") {
			content = [{ name: "<Select all contents>", type: "all_content" }, ...content];
		}
		opened_folders = content
			.map((x, i) =>
				x.type === "folder" &&
				(is_selected_entirely || selected.some((y) => y[0] === x.name))
					? i
					: null
			)
			.filter((x): x is number => x !== null);
	})();

	$: if (is_selected_entirely) {
		content.forEach((x) => {
			dispatch("check", {
				path: [...path, x.name],
				checked: true,
				type: x.type
			});
		});
	}

	const dispatch = createEventDispatcher<{
		check: { path: string[]; checked: boolean; type: "file" | "folder"  | "all_content"};
	}>();
	console.log("File tree selected:", selected);
</script>

<ul>
	{#each content as { type, name, valid }, i}
		<li>
			<span class="wrap">
				<Checkbox
					disabled={!interactive}
					value={selected.some(
						(x) => x[0] === name && x.length === 1
					)}
					on:change={(e) => {
						let checked = e.detail;
						dispatch("check", {
							path: [...path, name],
							checked,
							type
						
						});
						// It is faster to dispatch events for all children here than to filter through all 
						// contents in root directory in Directory Explorer
						if (type === "all_content" && checked) {
							content.filter((x) => path_next_to([...path, x.name], [...path, name]) && x.type !== "all_content").forEach((x) => {
								dispatch("check", {
									path: [...path, x.name],
									checked,
									type: x.type
								});
							});

						}
					}}
				/>

				{#if type === "folder"}
					<span
						class="icon"
						class:hidden={!opened_folders.includes(i)}
						on:click|stopPropagation={() => toggle_open_folder(i)}
						role="button"
						aria-label="expand directory"
						tabindex="0"
						on:keydown={({ key }) => {
							if (key === " " || key === "Enter") {
								toggle_open_folder(i);
							}
						}}><Arrow /></span
					>
				{:else if type === "file"}
					<span class="file-icon">
						<img src={FileIcon} alt="file icon" />
					</span>
				{/if}
				{name}
			</span>
			{#if type === "folder" && opened_folders.includes(i)}
				<svelte:self
					path={[...path, name]}
					selected={selected
						.filter((x) => x[0] === name)
						.map((x) => x.slice(1))}
						
					
					{interactive}
					{ls_fn}
					{file_count}
					valid_for_selection={valid}
					on:check
				/>
			{/if}
		</li>
	{/each}
</ul>

<style>
	.icon {
		display: inline-block;
		width: 18px;
		height: 18px;
		padding: 3px 2px 3px 3px;
		margin: 0;
		flex-grow: 0;
		display: inline-flex;
		justify-content: center;
		align-items: center;
		border-radius: 2px;
		cursor: pointer;
		transition: 0.1s;
		flex-shrink: 0;
	}

	.file-icon {
		display: inline-block;
		height: 20px;
		margin-left: -1px;
		margin: 0;
		flex-grow: 0;
		display: inline-flex;
		justify-content: center;
		align-items: center;

		transition: 0.1s;
	}

	.file-icon img {
		width: 100%;
		height: 100%;
	}

	.icon:hover {
		background: #eee;
	}

	.icon:hover :global(> *) {
		color: var(--block-info-text-color);
	}

	.icon :global(> *) {
		transform: rotate(90deg);
		transform-origin: 40% 50%;
		transition: 0.2s;
		color: var(--color-accent);
	}

	.no-checkbox {
		width: 18px;
		height: 18px;
	}

	.hidden :global(> *) {
		transform: rotate(0);
		color: var(--body-text-color-subdued);
	}

	ul {
		margin-left: 26px;
		padding-left: 0;
		list-style: none;
	}

	li {
		margin-left: 0;
		padding-left: 0;
		align-items: center;
		margin: 8px 0;
		font-family: var(--font-mono);
		font-size: var(--scale-00);
		overflow-wrap: anywhere;
		word-break: break-word;
	}

	.wrap {
		display: flex;
		gap: 8px;
		align-items: center;
	}
</style>
