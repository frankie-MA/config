local flavour_file = vim.fn.stdpath("config") .. "/lua/theme-flavour.lua"
local flavour = vim.fn.filereadable(flavour_file) == 1 and require("theme-flavour") or "mocha"

return {
    "catppuccin/nvim",
    name = "catppuccin",
    priority = 1000, -- загружать раньше всех плагинов
    opts = {
        flavour = flavour,
        integrations = {
            mason = true,
            which_key = true,
            treesitter = true,
        },
    },
    config = function(_, opts)
        require("catppuccin").setup(opts)
        vim.cmd.colorscheme("catppuccin")
    end,
}
