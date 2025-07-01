# Contributing to Valdris

Thank you for your interest in contributing to Valdris! This collaborative D&D campaign world grows richer with every contribution. Whether you're adding a mysterious ruin, crafting an NPC, or expanding the lore, your creativity helps make Valdris a living world.

## 🌟 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** (`git checkout -b feature/your-addition`)
4. **Make your changes** following the guidelines below
5. **Test your changes** in both Obsidian and browser
6. **Commit with a clear message** (`git commit -m "Add: The Whispering Forge ruins"`)
7. **Push to your fork** and submit a Pull Request

## 📝 Content Guidelines

### General Principles

- **Maintain consistency** with existing lore and themes
- **Keep it collaborative** - leave hooks for other contributors
- **Think modular** - content should work standalone or integrated
- **Stay system-agnostic** in lore (mechanics can be D&D 5E specific)
- **Be inclusive** in your writing and worldbuilding

### Writing Style

- **Present tense** for descriptions ("The tower stands..." not "The tower stood...")
- **Active voice** when possible
- **Show, don't tell** - use sensory details
- **Leave mysteries** - not everything needs explaining
- **Player perspective** - no secret DM information in main content

## 🔗 Link Formatting

### For GitHub Pages / Web Viewing

Since we maintain both an Obsidian vault and a web version via GitHub Pages, please follow these linking guidelines:

#### Internal Links
```markdown
<!-- Good - Full path from root -->
[Grimhaven](Settlements/Grimhaven.md)
[Tinker-Priests](Factions & Organizations/Tinker-Priests.md)

<!-- Bad - Assumes file is in root -->
[Grimhaven](Grimhaven.md)
```

#### From Subdirectories
When linking from files in subdirectories:
```markdown
<!-- From Settlements/Grimhaven.md -->
[Thymeris the Golden](../Architect Ruins/Thymeris the Golden.md)
[Welcome](../Welcome.md)
```

#### Non-Existent Links
If linking to planned but not-yet-created content:
```markdown
<!-- Remove the .md extension -->
The mysterious [Order of the Silver Key] guards ancient secrets...
```

### File Naming Conventions

- Use descriptive names: `The Singing Spires of Kelathon.md` not `spires.md`
- Spaces are fine: `Architect Ruins.md` not `architect-ruins.md`
- Maintain consistent capitalization
- Group related content in folders

## 📁 Directory Structure

```
Valdris/
├── Adventures/          # Ready-to-run quests and campaigns
├── Architect Ruins/     # Major ancient sites
├── Economics & Trade/   # Commerce and economy
├── Factions & Organizations/  # Groups and societies
├── Lore/               # History and world information
├── Music/              # Songs and musical culture
├── NPCs/               # Notable characters
├── Player Resources/   # Character creation and player info
├── Political Systems/  # Governance structures
├── Regions/            # Geographic areas
├── Settlements/        # Cities, towns, villages
├── Social Systems/     # Culture and society
├── Technology/         # Architect devices and innovations
└── Templates/          # Templates for new content
```

## 🏷️ Tagging System

Use consistent tags to help with organization:

- `#location` - Physical places
- `#npc` - Characters
- `#faction` - Organizations and groups
- `#lore` - Historical or world information
- `#quest` - Adventure hooks and missions
- `#item` - Artifacts, treasures, equipment
- `#architect` - Related to ancient technology
- `#recent-awakening` - Current events

## ✅ Contribution Checklist

Before submitting your PR, ensure:

- [ ] Links use full paths from vault root
- [ ] New content has appropriate tags
- [ ] Lore is consistent with existing material
- [ ] File names follow conventions
- [ ] No DM secrets in player-visible content
- [ ] Tested in both Obsidian and browser
- [ ] Spell-checked (especially "Valdris" not "Valderis")
- [ ] Added to relevant indexes or navigation

## 🎨 Types of Contributions

### New Locations
- Include physical description
- Add cultural/political context
- Create 2-3 adventure hooks
- Link to relevant factions/NPCs

### NPCs
- Provide appearance and personality
- Include motivations (public and secret)
- Add connections to places/factions
- Suggest how to use in games

### Adventures
- Clear objectives and hooks
- Scalable difficulty options
- Multiple possible outcomes
- Connections to larger world

### Lore Expansions
- Build on existing mysteries
- Add depth without closing doors
- Include multiple perspectives
- Reference existing content

## 🐛 Reporting Issues

Found something that needs fixing? Please [open an issue](https://github.com/offendingcommit/valdris/issues) with:

- Clear description of the problem
- Location (file path) where found
- Suggested fix if you have one
- Label appropriately (bug, inconsistency, typo, etc.)

## 💬 Getting Help

- Check existing content for examples
- Review recent PRs for style guidance
- Open an issue with questions
- Tag your PR as "needs feedback" if unsure

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [CC BY-SA 4.0](LICENSE) license as the rest of the project.

## 🙏 Thank You!

Every contribution makes Valdris more vibrant and exciting. Whether you're adding a single tavern or an entire region, you're helping create something special for the entire D&D community.

Happy worldbuilding! 🎲