module.exports = function(grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        jade: {
          compile: {
            options: {
              data: {
                debug: false
              },
              pretty: true,
            },
            files: [{
              expand: true,
              cwd: 'attract/src/jade',
              src: [ '**/*.jade' ],
              dest: 'attract/application/templates',
              ext: '.html'
            }]
          }
        },

        sass: {
            dist: {
                options: {
                    style: 'compressed'
                },
                files: {
                    'attract/application/static/assets/css/main.css': 'attract/src/sass/main.sass'
                }
            }
        },

        autoprefixer: {
            no_dest: { src: 'attract/application/static/assets/css/main.css' }
        },

        watch: {
            files: ['attract/src/sass/main.sass'],
            tasks: ['sass', 'autoprefixer'],
            jade: {
              files: 'attract/src/jade/**/*.jade',
              tasks: [ 'jade' ]
            },
        }
    });

    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-autoprefixer');
    grunt.loadNpmTasks('grunt-contrib-jade');

    grunt.registerTask('default', ['sass', 'autoprefixer', 'jade']);
};
